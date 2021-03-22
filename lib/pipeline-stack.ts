import * as codecommit from "@aws-cdk/aws-codecommit";
import * as codepipeline from "@aws-cdk/aws-codepipeline";
import * as codepipeline_actions from "@aws-cdk/aws-codepipeline-actions";
import { App, CfnOutput, Stack, StackProps } from "@aws-cdk/core";
import { CdkPipeline, SimpleSynthAction } from "@aws-cdk/pipelines";
import { VideoAnalyticsDeploymentStage } from "./pipeline-test-stage";

export class PipelineStack extends Stack {
  constructor(scope: App, id: string, props: StackProps) {
    super(scope, id, props);

    const repository = new codecommit.Repository(this, "codecommitRepo", {
      repositoryName: "video-analytics-for-ppe-compliance",
      description:
        "Sample implementation of video analytics solution on AWS with ML capabilities",
    });

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

    const deploymentStage = new VideoAnalyticsDeploymentStage(this, "Deploy", {
      env: { region: "us-west-2" },
    });
    cdkPipeline.addApplicationStage(deploymentStage);

    new CfnOutput(this, "CodeCommitRepoSshUrl", {
      value: repository.repositoryCloneUrlSsh,
      description: "Url for SSH access for CodeCommit Repository",
    });
  }

}
