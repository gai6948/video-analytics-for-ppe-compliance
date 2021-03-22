import * as cdk from "@aws-cdk/core";
import * as cognito from "@aws-cdk/aws-cognito";
import * as appsync from "@aws-cdk/aws-appsync";
import * as iam from "@aws-cdk/aws-iam";
import * as s3 from "@aws-cdk/aws-s3";
import * as cloudfront from "@aws-cdk/aws-cloudfront";
import * as nodejsLambda from "@aws-cdk/aws-lambda-nodejs";
import * as origins from "@aws-cdk/aws-cloudfront-origins";
import * as lambda from "@aws-cdk/aws-lambda";

export interface UIPortalStackProps extends cdk.StackProps {
  userPool: cognito.UserPool;
  identityPool: cognito.CfnIdentityPool;
  appClient: cognito.UserPoolClient;
  frameBucket: s3.Bucket;
  appsyncAPI: appsync.GraphqlApi;
}

export class UIPortalStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props: UIPortalStackProps) {
    super(scope, id, props);

    const portalUIBucket = new s3.Bucket(this, "PortalAssetsBucket", {
      encryption: s3.BucketEncryption.S3_MANAGED,
      cors: [
        {
          allowedMethods: [s3.HttpMethods.GET],
          allowedOrigins: ["*"],
          allowedHeaders: ["*"],
          id: "UICorsRule",
          maxAge: 3600,
        },
      ],
    });

    const setupLambda = new nodejsLambda.NodejsFunction(this, "SetupUILambda", {
      entry: "./src/lambda/setup-portal/index.js",
      handler: "handler",
      runtime: lambda.Runtime.NODEJS_12_X,
      timeout: cdk.Duration.minutes(10),
      environment: {
        COGNITO_IDENTITY_POOL: props.identityPool.ref,
        COGNITO_USERPOOL_ID: props.userPool.userPoolId,
        COGNITO_USERPOOLCLIENT_ID: props.appClient.userPoolClientId,
        TO_BUCKET: portalUIBucket.bucketName,
        REGION: "us-west-2",
        FRAME_BUCKET: props.frameBucket.bucketName,
        FROM_BUCKET: "aws-hkg-entsa-cf-quickstart-assets-bucket-us-west-2",
        FILE_BUCKET: portalUIBucket.bucketName,
        VERSION: "0.1",
      },
      bundling: {
          nodeModules: ['unzipper']
      }
    });

    setupLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["s3:GetObject"],
        resources: [
          "arn:aws:s3:::aws-hkg-entsa-cf-quickstart-assets-bucket-us-west-2/*",
        ],
      })
    );

    portalUIBucket.grantReadWrite(setupLambda);

    new cdk.CfnCustomResource(this, "SetupUICR", {
      serviceToken: setupLambda.functionArn,
    });

    const portalOAI = new cloudfront.OriginAccessIdentity(this, "UIOAI");

    const portalDistribution = new cloudfront.Distribution(
      this,
      "UIDistribution",
      {
        defaultBehavior: {
          origin: new origins.S3Origin(portalUIBucket, {
            originAccessIdentity: portalOAI,
          }),
        },
        defaultRootObject: "index.html",
      }
    );

    portalUIBucket.addToResourcePolicy(
      new iam.PolicyStatement({
        actions: ["s3:GetObject"],
        effect: iam.Effect.ALLOW,
        resources: [`arn:aws:s3:::${portalUIBucket.bucketName}/*`],
        principals: [
          new iam.CanonicalUserPrincipal(
            portalOAI.cloudFrontOriginAccessIdentityS3CanonicalUserId
          ),
        ],
      })
    );

    new cdk.CfnOutput(this, "MonitoringPortalUrl", {
      value: portalDistribution.distributionDomainName,
      description: "URL of the PPEMonitoring portal",
    });
  }
}
