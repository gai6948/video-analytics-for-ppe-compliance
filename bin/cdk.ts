#!/usr/bin/env node
import "source-map-support/register";
import * as cdk from "@aws-cdk/core";
import { SharedInfraStack } from "../lib/shared-infra";
import { GraphQLStack } from "../lib/graphql-layer-stack";
import { FrameProcessorStack } from "../lib/frame-processor-stack";
import { FrameParserStack } from "../lib/frame-parser-stack";
import { MonitoringDashboard } from "../lib/dashboard-stack";

const app = new cdk.App();

const infraStack = new SharedInfraStack(app, "VideoMonitoringInfraStack", {
  description: "Shared infrastructure for video monitoring services",
});

const graphQLLayerStack = new GraphQLStack(app, "GraphQLLayerStack", {
  description:
    "Stack containing the GraphQL API, its resolver functions and Cognito User Pool",
});

const frameParserStack = new FrameParserStack(app, "KVSFrameParserStack", {
  cluster: infraStack.cluster,
  privateSubnets: infraStack.privateSubnets,
});

const frameProcessorStack = new FrameProcessorStack(
  app,
  "FrameProcessorStack",
  {
    targetGqlApi: graphQLLayerStack.appsyncAPI,
    cognitoAuthRole: graphQLLayerStack.cognitoAuthRole,
    rawFrameBucket: frameParserStack.rawFrameBucket,
    description:
      "A stack that contains a Kinesis Data Streams, a Lambda consumer processing the frames, and an S3 bucket storing the frames",
  }
);

// const cwDashboardStack = new MonitoringDashboard(
//   app,
//   "CloudWatchDashboardStack",
//   {
//     ppeDetectorFunction: frameProcessorStack.frameProcessorFunction,
//     faceDetectorFunction: frameProcessorStack.faceDetectorFunction,
//     ecsCluster: infraStack.cluster,
//     // javaParserFargateService: frameParserStack.kvsFrameParserService,
//     fargateAutoScalerFunc: frameParserStack.fargateAutoScalerFunction,
//     appsyncAPI: graphQLLayerStack.appsyncAPI,
//     frameParserLogGroup: frameParserStack.kvsFrameParserLogGroup,
//   }
// );

// cwDashboardStack.addDependency(frameProcessorStack);

app.synth();
