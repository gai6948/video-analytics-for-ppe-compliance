import { Construct, Stage, StageProps } from "@aws-cdk/core";
import { SharedInfraStack } from "./shared-infra";
import { FrameParserStack } from "./frame-parser-stack";
import { FrameProcessorStack } from "./frame-processor-stack";
import { GraphQLStack } from "./graphql-layer-stack";
import { MonitoringDashboard } from "./dashboard-stack";
import { UIPortalStack } from "./ui-portal-stack";

export class VideoAnalyticsDeploymentStage extends Stage {
  constructor(scope: Construct, id: string, props?: StageProps) {
    super(scope, id, props);

    const infraStack = new SharedInfraStack(this, "VideoAnalyticsInfraStack", {
      description: "Shared infrastructure for video analytics services",
    });

    const graphQLLayerStack = new GraphQLStack(this, "GraphQLLayerStack", {
      description:
        "Stack containing the GraphQL API, its resolver functions and Cognito User Pool",
    });

    const frameProcessorStack = new FrameProcessorStack(
      this,
      "FrameProcessorStack",
      {
        targetGqlApi: graphQLLayerStack.appsyncAPI,
        cognitoAuthRole: graphQLLayerStack.cognitoAuthRole,
        pythonGQLLayer: graphQLLayerStack.pythonGQLLayer,
        firehoseStream: graphQLLayerStack.firehoseStream,
        description:
          "A stack that contains Lambda consumers processing the frames, and S3 buckets storing the frames",
      }
    );

    const frameParserStack = new FrameParserStack(this, "KVSFrameParserStack", {
      cluster: infraStack.cluster,
      privateSubnets: infraStack.privateSubnets,
      rawFrameBucket: frameProcessorStack.rawFrameBucket
    });

    frameParserStack.addDependency(
      frameProcessorStack,
      "Wait for Kinesis Data Streams setup"
    );

    const cwDashboardStack = new MonitoringDashboard(this, "CloudWatchDashboardStack", {
      ppeDetectorFunction: frameProcessorStack.frameProcessorFunction,
      faceDetectorFunction: frameProcessorStack.faceDetectorFunction,
      ecsCluster: infraStack.cluster,
      fargateAutoScalerFunc: frameParserStack.fargateAutoScalerFunction,
      appsyncAPI: graphQLLayerStack.appsyncAPI,
      frameParserLogGroup: frameParserStack.kvsFrameParserLogGroup,
    });

    cwDashboardStack.addDependency(frameProcessorStack);

    const uiPortalStack = new UIPortalStack(this, "WebUIPortalStack", {
      appClient: graphQLLayerStack.appClient,
      appsyncAPI: graphQLLayerStack.appsyncAPI,
      frameBucket: frameProcessorStack.processedframeBucket,
      identityPool: graphQLLayerStack.identityPool,
      userPool: graphQLLayerStack.userPool,
    });

    cwDashboardStack.addDependency(frameProcessorStack);

  }
}
