import * as cdk from "@aws-cdk/core";
import * as ecs from "@aws-cdk/aws-ecs";
import * as ec2 from "@aws-cdk/aws-ec2";
import * as iam from "@aws-cdk/aws-iam";
import * as logs from '@aws-cdk/aws-logs';
import * as lambda from '@aws-cdk/aws-lambda';
import * as events from '@aws-cdk/aws-events';
import * as targets from '@aws-cdk/aws-events-targets';
import * as ddb from '@aws-cdk/aws-dynamodb';
import * as s3 from '@aws-cdk/aws-s3';

export interface FrameParserStackProps extends cdk.StackProps {
  cluster: ecs.Cluster;
  privateSubnets: ec2.SubnetSelection;
  rawFrameBucket: s3.Bucket;
}

export class FrameParserStack extends cdk.Stack {
  public readonly frameParserFargateTaskRole: iam.IRole;
  public readonly kvsFrameParserLogGroup: logs.LogGroup;
  public readonly fargateAutoScalerFunction: lambda.Function;

  constructor(scope: cdk.Construct, id: string, props: FrameParserStackProps) {
    super(scope, id, props);

    // Give our fargate container task the premission to read from Kinesis Video Streams
    const kvsReadPolicy = new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      resources: ["*"],
      actions: ["kinesisvideo:DescribeStream", "kinesisvideo:Get*"],
    });

    const frameParserTaskDef = new ecs.FargateTaskDefinition(
      this,
      "KVSFrameParserFargateTaskDef",
      {
        cpu: 256,
        memoryLimitMiB: 512,
      }
    );

    frameParserTaskDef.addToTaskRolePolicy(kvsReadPolicy);
    props.rawFrameBucket.grantPut(frameParserTaskDef.taskRole);
    this.frameParserFargateTaskRole = frameParserTaskDef.taskRole;

    const kvsFrameParserLogGroup = new logs.LogGroup(this, "KvsFrameParserLogGroup", {
      retention: logs.RetentionDays.TWO_MONTHS
    });

    const kvsFrameParserContainer = frameParserTaskDef.addContainer(
      "kvs-parse-frame",
      {
        // image: ecs.ContainerImage.fromAsset(`${__dirname}/../src/ecs/kvs-frame-parser`),
        image: ecs.ContainerImage.fromRegistry("public.ecr.aws/j9q5t3v2/video-analytics-for-ppe-kvs2s3:v1"),
        logging: ecs.LogDriver.awsLogs({
          streamPrefix: 'kvs-frame-parser',
          logGroup: kvsFrameParserLogGroup
        }),
        environment: {
          CAMERA_NAME: "kvs_example_camera_stream",
          S3_BUCKET_NAME: props.rawFrameBucket.bucketName,
          AWS_DEFAULT_REGION: "us-west-2",
          PROCESS_RATE_IN_FPS: "1"
        },
      }
    );
    
    const consumerMappingTable = new ddb.Table(this, "KVSConsumerMappingTable", {
      partitionKey: {
        name: "cameraId",
        type: ddb.AttributeType.STRING
      },
      billingMode: ddb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY
    });

    const parserAutoScaler = new lambda.Function(this, "KvsParserAutoScaler", {
      runtime: lambda.Runtime.PYTHON_3_8,
      code: lambda.Code.fromAsset(`${__dirname}/../src/lambda/kvs-parser-autoscaler`),
      handler: "lambda.handler",
      environment: {
        FARGATE_CLUSTER_NAME: props.cluster.clusterName,
        SUBNET_ONE: props.privateSubnets.subnets ? props.privateSubnets.subnets[0].subnetId : "",
        SUBNET_TWO: props.privateSubnets.subnets ? props.privateSubnets.subnets[1].subnetId : "",
        TASK_DEF_ARN: frameParserTaskDef.taskDefinitionArn,
        TASK_MAPPING_TABLE: consumerMappingTable.tableName,
      },
      timeout: cdk.Duration.seconds(10)
    });

    this.fargateAutoScalerFunction = parserAutoScaler;
    consumerMappingTable.grantReadWriteData(parserAutoScaler);

    parserAutoScaler.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["cloudwatch:Get*", "ecs:*", "iam:PassRole"],
      resources: ["*"],
    }));

    this.frameParserFargateTaskRole.grantPassRole(parserAutoScaler.grantPrincipal);
    parserAutoScaler.role?.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonKinesisVideoStreamsReadOnlyAccess"));

    const autoScalerSchedule = new events.Rule(this, "KvsAutoScalerRule", {
      schedule: events.Schedule.expression("rate(2 minutes)"),
    });

    autoScalerSchedule.addTarget(new targets.LambdaFunction(parserAutoScaler));

    // this.kvsFrameParserService = kvsFrameParserService;
    this.kvsFrameParserLogGroup = kvsFrameParserLogGroup;

  }
}
