import {
  CfnOutput,
  Construct,
  Duration,
  Stack,
  StackProps,
} from "@aws-cdk/core";
import * as kinesis from "@aws-cdk/aws-kinesis";
import * as lambda from "@aws-cdk/aws-lambda";
import * as pythonLambda from "@aws-cdk/aws-lambda-python";
import * as iam from "@aws-cdk/aws-iam";
import * as s3 from "@aws-cdk/aws-s3";
import * as s3n from "@aws-cdk/aws-s3-notifications";
import * as appsync from "@aws-cdk/aws-appsync";
import * as assets from "@aws-cdk/aws-s3-assets";
import * as sns from "@aws-cdk/aws-sns";
import * as sub from "@aws-cdk/aws-sns-subscriptions";
import * as sqs from "@aws-cdk/aws-sqs";
import * as events from "@aws-cdk/aws-lambda-event-sources";

export interface FrameProcessorStackProps extends StackProps {
  targetGqlApi: appsync.GraphqlApi;
  cognitoAuthRole: iam.Role;
}

export class FrameProcessorStack extends Stack {
  public readonly frameProcessorFunction: lambda.Function;
  public readonly faceDetectorFunction: lambda.Function;
  public readonly newFrameConsumer: kinesis.CfnStreamConsumer;
  public rawFrameBucket: s3.Bucket;
  public processedframeBucket: s3.Bucket;

  constructor(
    scope: Construct,
    id: string,
    props: FrameProcessorStackProps
  ) {
    super(scope, id, props);

    // Create S3 bucket for storing raw image frame extracted from KVS
    const rawFrameBucket = new s3.Bucket(this, "RawFrameBucket", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [
        {
          enabled: true,
          expiration: Duration.hours(24),
          abortIncompleteMultipartUploadAfter: Duration.days(1)
        }
      ]
    });
    this.rawFrameBucket = rawFrameBucket;

    // When frame is uploaded to the raw frame bucket, an event message will be sent from S3 -> SNS -> SQS, then picked up
    // by the PPE Lambda function
    const newFrameTopic = new sns.Topic(this, "NewFrameTopic");
    const newFrameQueue = new sqs.Queue(this, "NewFrameQueue", {
      retentionPeriod: Duration.days(1),
      encryption: sqs.QueueEncryption.KMS_MANAGED,
      visibilityTimeout: Duration.seconds(10),
    });
    newFrameTopic.addSubscription(new sub.SqsSubscription(newFrameQueue));
    rawFrameBucket.addEventNotification(s3.EventType.OBJECT_CREATED_PUT, new s3n.SnsDestination(newFrameTopic));

    // Create S3 bucket for storing the frames
    const processedFrameBucket = new s3.Bucket(this, "FrameBucket", {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      lifecycleRules: [
        {
          id: "30IA90Glacier",
          transitions: [
            {
              storageClass: s3.StorageClass.INFREQUENT_ACCESS,
              transitionAfter: Duration.days(30),
            },
            {
              storageClass: s3.StorageClass.GLACIER,
              transitionAfter: Duration.days(90),
            },
          ],
        },
      ],
      cors: [
        {
          allowedMethods: [s3.HttpMethods.HEAD, s3.HttpMethods.GET],
          allowedOrigins: ["*"],
          exposedHeaders: [
            "x-amz-request-id",
            "ETag",
            "Content-Length",
            "Content-Type",
          ],
          allowedHeaders: ["*"],
        },
      ],
    });
    this.processedframeBucket = processedFrameBucket;

    const violationAlarmTopic = new sns.Topic(this, "PPEViolationTopic", {
      displayName: "PPE Violation Alarm Topic"
    });

    // Since the Lambda layer package is >50 MB, we need to bundle it as asset to S3
    // const pythonLambdaLayerAsset = new assets.Asset(
    //   this,
    //   "PythonLayerPackage",
    //   {
    //     path: `./build/package/`,
    //   }
    // );

    // Create layer that is common across Python Lambda functions
    // const pythondetectorLayer = new lambda.LayerVersion(
    //   this,
    //   "PythonDetectorLayerVersion",
    //   {
    //     code: lambda.Code.fromBucket(
    //       pythonLambdaLayerAsset.bucket,
    //       pythonLambdaLayerAsset.s3ObjectKey
    //     ),
    //     compatibleRuntimes: [lambda.Runtime.PYTHON_3_8],
    //     description: "Common Python packages for image processing",
    //   }
    // );

    const pythonDetectorLayer = new pythonLambda.PythonLayerVersion(this, "PythonDetectorLayer", {
      entry: "./src/lambda/layers/detectors-common/",
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_8],
    });

    // Create Lambda PPE Processor
    const ppeProcessorFunction = new pythonLambda.PythonFunction(
      this,
      "PPEFrameProcessor",
      {
        entry: "./src/lambda/ppe-detector-function",
        index: "lambda.py",
        handler: "handler",
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: Duration.seconds(7),
        tracing: lambda.Tracing.ACTIVE,
        retryAttempts: 0,
        layers: [pythonDetectorLayer],
        reservedConcurrentExecutions: 5,
        environment: {
          GRAPHQL_API_ENDPOINT: props.targetGqlApi.graphqlUrl,
          S3_BUCKET: processedFrameBucket.bucketName,
          MIN_DETECTION_CONFIDENCE: "70",
          TARGET_IMAGE_WIDTH: "480",
          TARGET_IMAGE_HEIGHT: "320",
          SNS_TOPIC_ARN: violationAlarmTopic.topicArn
        },
        maxEventAge: Duration.seconds(60),
        memorySize: 256,
      }
    );

    ppeProcessorFunction.node.addDependency(processedFrameBucket);

    // Grant access to the Lambda function
    rawFrameBucket.grantRead(ppeProcessorFunction);
    processedFrameBucket.grantPut(ppeProcessorFunction);
    violationAlarmTopic.grantPublish(ppeProcessorFunction);

    props.targetGqlApi.grantMutation(ppeProcessorFunction);
    props.targetGqlApi.grantQuery(ppeProcessorFunction);

    this.frameProcessorFunction = ppeProcessorFunction;

    ppeProcessorFunction.addEventSource(new events.SqsEventSource(newFrameQueue, {
      batchSize: 1,
    }));

    // Grant PPE processor function to call PPE API
    const ppeDetectorPolicyStmt = new iam.PolicyStatement({
      resources: ["*"],
      actions: ["rekognition:DetectProtectiveEquipment"],
    });
    ppeProcessorFunction.addToRolePolicy(ppeDetectorPolicyStmt);

    // Create the face detection Lambda
    const faceDetectorFunction = new pythonLambda.PythonFunction(this, "FaceDetector", {
      entry: "./src/lambda/face-detector-function",
      index: "lambda.py",
      handler: "handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      timeout: Duration.seconds(30),
      tracing: lambda.Tracing.ACTIVE,
      layers: [pythonDetectorLayer],
      memorySize: 256,
      environment: {
        GRAPHQL_API_ENDPOINT: props.targetGqlApi.graphqlUrl,
        FRAME_BUCKET_NAME: processedFrameBucket.bucketName,
        MIN_CONFIDENCE_THRESHOLD: '90',
        FACE_COLLECTION_ID: 'test-collection-01'
      }
    });

    this.faceDetectorFunction = faceDetectorFunction;
    processedFrameBucket.grantReadWrite(faceDetectorFunction);
    props.targetGqlApi.grantMutation(faceDetectorFunction);
    faceDetectorFunction.addToRolePolicy(new iam.PolicyStatement({
      actions: ["rekognition:SearchFacesByImage"],
      effect: iam.Effect.ALLOW,
      resources: ["*"]
    }));

    violationAlarmTopic.addSubscription(new sub.LambdaSubscription(faceDetectorFunction));


    new CfnOutput(this, "FrameBucketName", {
      value: processedFrameBucket.bucketName,
      description: "Name of the S3 bucket storing the image frames",
    });
  }
}
