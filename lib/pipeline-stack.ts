import * as codecommit from "@aws-cdk/aws-codecommit";
import * as codepipeline from "@aws-cdk/aws-codepipeline";
import * as codepipeline_actions from "@aws-cdk/aws-codepipeline-actions";
import { App, CfnOutput, Stack, StackProps } from "@aws-cdk/core";
import * as iam from "@aws-cdk/aws-iam";
import { CdkPipeline, PublishAssetsAction, SimpleSynthAction } from "@aws-cdk/pipelines";
import { VideoAnalyticsDeploymentStage } from "./pipeline-test-stage";

export class PipelineStack extends Stack {
  constructor(scope: App, id: string, props: StackProps) {
    super(scope, id, props);

    // Create a CodeCommit repository
    const repository = new codecommit.Repository(this, "codecommitRepo", {
      repositoryName: "video-analytics-for-ppe-compliance",
      description:
        "Sample implementation of video analytics solution on AWS with ML capabilities",
    });

    // CDK pipeline
    const srcArtifact = new codepipeline.Artifact(
      "video-analytics-src-artifact"
    );
    const cloudAssemblyArtifact = new codepipeline.Artifact(
      "video-analytics-cloudass-artifact"
    );

    const cdkPipeline = new CdkPipeline(this, "VideoAnalyticsCDKPipeline", {
      crossAccountKeys: true,
      cloudAssemblyArtifact,
      sourceAction: new codepipeline_actions.CodeCommitSourceAction({
        actionName: "Source",
        output: srcArtifact,
        repository,
      }),
      synthAction: new SimpleSynthAction({
        sourceArtifact: srcArtifact,
        cloudAssemblyArtifact,
        installCommands: [
          "npm ci",
          "npm i --save-dev esbuild@0",
          "docker login --username gc6948 -p 404cb1cb-c7c0-491d-a88d-0d43dd7b0460"
        ],
        buildCommands: [
          "echo Preparing CDK deployment...",
          "npm run build",
        ],
        synthCommand: "npx cdk synth",
        environment: {
          privileged: true,
        },
      }),
      selfMutating: true
    });

    const deploymentStage = new VideoAnalyticsDeploymentStage(this, "Deployment", {
      env: { region: "us-west-2" },
    });
    cdkPipeline.addApplicationStage(deploymentStage);

    new CfnOutput(this, "CodeCommitRepoSshUrl", {
      value: repository.repositoryCloneUrlSsh,
      description: "Url for SSH access for CodeCommit Repository",
    });
  }

  private static addECRLogin (pipeline: CdkPipeline, sourceECRs: string[]) {
    for (const action of pipeline.stage('Assets')?.actions) {
      const actionProperties = action.actionProperties;
      if (actionProperties.actionName.startsWith('Docker')) {
        // workaround for https://github.com/aws/aws-cdk/issues/10999
        const publishAction = action as PublishAssetsAction;
        const commands: string[] = (publishAction as any).commands;
        for (const sourceECR of sourceECRs) {
          // NOTE: this makes the simplifying assumption that the sourceECR is in the same region as the pipeline
          const command = `aws ecr get-login-password --region ${Stack.of(pipeline).region} | docker login --username AWS --password-stdin ${sourceECR}`;
          if (!commands.includes(command)) {
            // login needs to happen before the asset publication (that's where docker images are built)
            commands.unshift(command);
          }
        }

        new iam.Policy(pipeline, 'AllowECRLoginAndPull', {
          statements: [
            new iam.PolicyStatement({
              actions: [
                'ecr:GetAuthorizationToken',
                'ecr:GetDownloadUrlForLayer',
                'ecr:BatchGetImage',
              ],
              resources: ['*'],
              sid: 'AllowECRLoginAndPull',
            }),
          ],
        }).attachToRole(actionProperties.role!);
      }
    }
  }

}
