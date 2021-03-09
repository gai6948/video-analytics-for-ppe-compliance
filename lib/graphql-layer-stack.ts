import {
  CfnOutput,
  Construct,
  Duration,
  RemovalPolicy,
  Stack,
  StackProps,
} from "@aws-cdk/core";
import * as appsync from "@aws-cdk/aws-appsync";
import * as cognito from "@aws-cdk/aws-cognito";
import * as kinesis from "@aws-cdk/aws-kinesis";
import * as iam from "@aws-cdk/aws-iam";
import * as dynamodb from "@aws-cdk/aws-dynamodb";
import * as es from "@aws-cdk/aws-elasticsearch";
import * as cr from "@aws-cdk/custom-resources";
import * as pythonLambda from "@aws-cdk/aws-lambda-python";
import * as lambda from "@aws-cdk/aws-lambda";
import * as events from "@aws-cdk/aws-lambda-event-sources";

export interface GraphQLStackProps extends StackProps {}

// This stack holds the AppSync resources (AppSync API, resolvers, Cognito user pool, etc)
export class GraphQLStack extends Stack {
  public appsyncAPI: appsync.GraphqlApi;
  public cognitoAuthRole: iam.Role;
  public cameraFrameTable: dynamodb.Table;
  public pythonGQLLayer: pythonLambda.PythonLayerVersion;
  public aesLoaderLambda: pythonLambda.PythonFunction;

  constructor(scope: Construct, id: string, props?: GraphQLStackProps) {
    super(scope, id, props);

    // Cognito user pool for API access control
    const cognitoUserPool = new cognito.UserPool(
      this,
      "VideoAnalyticsUserPool",
      {
        autoVerify: {
          email: true,
          phone: false,
        },
        selfSignUpEnabled: true,
        removalPolicy: RemovalPolicy.DESTROY,
      },
    );
    const aesUserPoolDomain = cognitoUserPool.addDomain('aes-auth-userpool', {
      cognitoDomain: {
        domainPrefix: 'aesauth'
      }
    });

    const portalAppClient = cognitoUserPool.addClient("portalAppClient");

    const cognitoIdentityPool = new cognito.CfnIdentityPool(
      this,
      "VideoAnalyticsIdentityPool",
      {
        allowUnauthenticatedIdentities: true,
        cognitoIdentityProviders: [
          {
            clientId: portalAppClient.userPoolClientId,
            providerName: cognitoUserPool.userPoolProviderName,
          },
        ],
      }
    );

    const authRole = new iam.Role(this, "CognitoAuthRole", {
      assumedBy: new iam.WebIdentityPrincipal(
        "cognito-identity.amazonaws.com",
        {
          StringEquals: {
            "cognito-identity.amazonaws.com:aud": cognitoIdentityPool.ref,
          },
          "ForAnyValue:StringEquals": {
            "cognito-identity.amazonaws.com:amr": "authenticated",
          },
        }
      ),
      description: "Role assumed by authenticated users",
    });

    const unAuthRole = new iam.Role(this, "CognitoUnAuthRole", {
      assumedBy: new iam.WebIdentityPrincipal(
        "cognito-identity.amazonaws.com",
        {
          StringEquals: {
            "cognito-identity.amazonaws.com:aud": cognitoIdentityPool.ref,
          },
          "ForAnyValue:StringEquals": {
            "cognito-identity.amazonaws.com:amr": "unauthenticated",
          },
        }
      ),
      description: "Role assumed by unauthenticated users",
    });

    authRole.node.addDependency(cognitoIdentityPool);
    this.cognitoAuthRole = authRole;
    authRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["s3:GetObject"],
        resources: ["arn:aws:s3:::*framebucket*/*"],
      })
    );
    authRole.addToPolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["s3:ListBucket"],
        resources: ["arn:aws:s3:::*framebucket*"],
      })
    );

    const cognitoRoleMapping = new cognito.CfnIdentityPoolRoleAttachment(
      this,
      "VideoMonitoringIdentityRoleMapping",
      {
        identityPoolId: cognitoIdentityPool.ref,
        roleMappings: {
          cognito: {
            identityProvider: "cognito-idp.us-west-2.amazonaws.com/".concat(
              cognitoUserPool.userPoolId,
              ":",
              portalAppClient.userPoolClientId
            ),
            ambiguousRoleResolution: "AuthenticatedRole",
            type: "Token",
          },
        },
        roles: {
          authenticated: authRole.roleArn,
          unauthenticated: unAuthRole.roleArn,
        },
      }
    );

    const appsyncAPI = new appsync.GraphqlApi(this, "AppSyncAPI", {
      name: "video-analytics-for-ppe-gql-api",
      xrayEnabled: true,
      schema: appsync.Schema.fromAsset("./src/graphql/schema.graphql"),
      logConfig: {
        excludeVerboseContent: false,
        fieldLogLevel: appsync.FieldLogLevel.ALL,
      },
      authorizationConfig: {
        defaultAuthorization: {
          authorizationType: appsync.AuthorizationType.IAM,
        },
        additionalAuthorizationModes: [
          {
            authorizationType: appsync.AuthorizationType.USER_POOL,
            userPoolConfig: {
              userPool: cognitoUserPool,
              defaultAction: appsync.UserPoolDefaultAction.ALLOW,
            },
          },
          {
            authorizationType: appsync.AuthorizationType.API_KEY,
          },
        ],
      },
    });

    this.appsyncAPI = appsyncAPI;

    appsyncAPI.grantSubscription(authRole);
    appsyncAPI.grantQuery(authRole);

    // DynamoDB table to store camera-frame mapping
    const cameraFrameTable = new dynamodb.Table(this, "CameraFrameTable", {
      partitionKey: {
        name: "cameraId",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "ts",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 3,
      writeCapacity: 5,
      timeToLiveAttribute: 'ttl',
      removalPolicy: RemovalPolicy.DESTROY,
    });

    this.cameraFrameTable = cameraFrameTable;

    // DynamoDB table to store detected PPE alarm
    const ppeAlarmTable = new dynamodb.Table(this, "PPEAlarmTable", {
      partitionKey: {
        name: "cameraId",
        type: dynamodb.AttributeType.STRING,
      },
      sortKey: {
        name: "ts",
        type: dynamodb.AttributeType.STRING,
      },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: RemovalPolicy.DESTROY,
    });

    const cameraFrameDataSource = appsyncAPI.addDynamoDbDataSource(
      "CameraFrameTableDatasource",
      cameraFrameTable,
      {
        description: "DynamoDB table storing camera-to-latest-frame mapping",
      }
    );

    cameraFrameDataSource.createResolver({
      typeName: "Mutation",
      fieldName: "injestFrame",
      requestMappingTemplate: appsync.MappingTemplate.fromFile(
        "./src/graphql/vtl/injestFrameRequest.vtl"
      ),
      responseMappingTemplate: appsync.MappingTemplate.dynamoDbResultItem(),
    });

    cameraFrameDataSource.createResolver({
      typeName: "Query",
      fieldName: "listCamera",
      requestMappingTemplate: appsync.MappingTemplate.dynamoDbScanTable(),
      responseMappingTemplate: appsync.MappingTemplate.dynamoDbResultList(),
    });

    const ppeAlarmDataSource = appsyncAPI.addDynamoDbDataSource(
      "PPEAlarmTableDatasource",
      ppeAlarmTable,
      {
        description: "DynamoDB table storing PPE Alarms",
      }
    );

    ppeAlarmDataSource.createResolver({
      typeName: "Mutation",
      fieldName: "newAlarm",
      requestMappingTemplate: appsync.MappingTemplate.fromFile(
        "./src/graphql/vtl/newAlarmRequest.vtl"
      ),
      responseMappingTemplate: appsync.MappingTemplate.dynamoDbResultItem()
    });
    
    ppeAlarmDataSource.createResolver({
      typeName: "Query",
      fieldName: "listAlarm",
      requestMappingTemplate: appsync.MappingTemplate.fromFile("./src/graphql/vtl/listAlarmRequest.vtl"),
      responseMappingTemplate: appsync.MappingTemplate.fromFile("./src/graphql/vtl/listAlarmResponse.vtl")
    });

    // Role for AES to configure Cognito
    const aesCognitoRole = new iam.Role(this, "CognitoAccessForAmazonES", {
      assumedBy: new iam.ServicePrincipal("es.amazonaws.com")
    });

    aesCognitoRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName("AmazonESCognitoAccess"));

    const aesResourcePolicy = new iam.PolicyDocument({
      statements: [
        new iam.PolicyStatement({
          effect: iam.Effect.ALLOW,
          principals: [this.cognitoAuthRole],
          actions: ["es:Http*"],
          resources: ["*"]
        })
      ]
    }).toJSON();

    const cfnEsDomain = new es.CfnDomain(this, "AESDomain", {
      advancedSecurityOptions: {
        enabled: false,
      },
      cognitoOptions: {
        enabled: true,
        userPoolId: cognitoUserPool.userPoolId,
        identityPoolId: cognitoIdentityPool.ref,
        roleArn: aesCognitoRole.roleArn,
      },
      elasticsearchVersion: "7.9",
      nodeToNodeEncryptionOptions: {
        enabled: true
      },
      encryptionAtRestOptions: {
        enabled: true
      },
      domainEndpointOptions: {
        enforceHttps: true,
      },
      ebsOptions: {
        ebsEnabled: true,
        volumeSize: 30,
        volumeType: "gp2"
      },
      accessPolicies: aesResourcePolicy,
    });
    cfnEsDomain.applyRemovalPolicy(RemovalPolicy.DESTROY);

    authRole.addToPolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: ["es:Http*"],
      resources: [cfnEsDomain.getAtt("Arn").toString()]
    }));

    // const esDomain = new es.Domain(this, "ESDomain", {
    //   version: es.ElasticsearchVersion.V7_1,
    //   enforceHttps: true,
    //   nodeToNodeEncryption: true,
    //   encryptionAtRest: {
    //     enabled: true,
    //   },
    //   fineGrainedAccessControl: {
    //     masterUserName: "monitor-admin",
    //     masterUserPassword: cdkSecAESPassword
    //   },
    //   logging: {
    //     auditLogEnabled: true,
    //   },
    // });

    // this.esDomain = esDomain;

    // Create a Kinesis Data Stream for replicate frame data written to DynamoDB
    const replicationStream = new kinesis.Stream(this, "replicationStream", {
      shardCount: 1,
    });

    // Python lambda layer for GQL/REST libraries and middleware
    const pythonGQLLayer = new pythonLambda.PythonLayerVersion(this, "PythonGQLLayer", {
      entry: "./src/lambda/layers/python-gql",
      compatibleRuntimes: [lambda.Runtime.PYTHON_3_8],
      description: "Python Lambda GQL/REST libraries and middleware"
    });
    this.pythonGQLLayer = pythonGQLLayer;

    // Lambda handler to load data to AES, and delete DDB entries
    const aesLoaderLambda = new pythonLambda.PythonFunction(
      this,
      "DynamoDBToAESLoader",
      {
        entry: "./src/lambda/aes-loader",
        handler: "handler",
        index: "index.py",
        runtime: lambda.Runtime.PYTHON_3_8,
        timeout: Duration.seconds(10),
        layers: [pythonGQLLayer],
        environment: {
          AES_HOST_URL: cfnEsDomain.getAtt("DomainEndpoint").toString(),
        },
      }
    );
    this.aesLoaderLambda = aesLoaderLambda;

    aesLoaderLambda.addToRolePolicy(new iam.PolicyStatement({
      effect: iam.Effect.ALLOW,
      actions: [
        "es:ESHttpPost",
        "es:ESHttpPut",
        "es:ESHttpDelete",
      ],
      resources: [cfnEsDomain.getAtt("Arn").toString()]
    }));
    // esDomain.grantIndexWrite("ppe_monitoring", aesLoaderLambda);

    aesLoaderLambda.addEventSource(new events.KinesisEventSource(replicationStream, {
      startingPosition: lambda.StartingPosition.LATEST,
      batchSize: 100,
      enabled: true,
      bisectBatchOnError: true,
      maxBatchingWindow: Duration.minutes(5),
    }));

    const cfnDDBServRole = new iam.CfnServiceLinkedRole(
      this,
      "DDBServiceLinkedRole",
      {
        awsServiceName: "kinesisreplication.dynamodb.amazonaws.com",
      }
    );

    const ddbToKinesis = new cr.AwsCustomResource(
      this,
      "CustomResourceDDBtoKinesis",
      {
        policy: cr.AwsCustomResourcePolicy.fromStatements([
          new iam.PolicyStatement({
            actions: [
              "dynamodb:EnableKinesisStreamingDestination",
              "dynamodb:DisableKinesisStreamingDestination",
              "dynamodb:DescribeKinesisStreamingDestination",
            ],
            effect: iam.Effect.ALLOW,
            resources: [cameraFrameTable.tableArn],
          }),
          new iam.PolicyStatement({
            actions: ["kinesis:*"],
            effect: iam.Effect.ALLOW,
            resources: [replicationStream.streamArn],
          }),
        ]),
        onCreate: {
          service: "DynamoDB",
          action: "enableKinesisStreamingDestination",
          parameters: {
            StreamArn: replicationStream.streamArn,
            TableName: cameraFrameTable.tableName,
          },
          physicalResourceId: cr.PhysicalResourceId.of(Date.now().toString()),
        },
        onDelete: {
          service: "DynamoDB",
          action: "disableKinesisStreamingDestination",
          parameters: {
            StreamArn: replicationStream.streamArn,
            TableName: cameraFrameTable.tableName,
          },
          physicalResourceId: cr.PhysicalResourceId.of(Date.now().toString()),
        },
        installLatestAwsSdk: true,
      }
    );

    ddbToKinesis.node.addDependency(cameraFrameTable);
    ddbToKinesis.node.addDependency(replicationStream);

    cameraFrameTable.grantFullAccess(ddbToKinesis);
    replicationStream.grant(ddbToKinesis, "*");

    new CfnOutput(this, "GraphQLAPIUrl", {
      value: appsyncAPI.graphqlUrl,
      description: "URL to the GraphQL API",
    });

    if (appsyncAPI.apiKey) {
      new CfnOutput(this, "DefaultAPIKey", {
        value: appsyncAPI.apiKey,
        description: "Default AppSync API key generated by CDK",
      });
    }

    new CfnOutput(this, "CognitoUserPoolId", {
      value: cognitoUserPool.userPoolId,
      description: "Id of the Cognito User Pool",
    });

    new CfnOutput(this, "CognitoIdentityPoolId", {
      value: cognitoIdentityPool.ref,
      description: "Id of the Cognito Identity Pool",
    });

    new CfnOutput(this, "CognitoAppClientId", {
      value: portalAppClient.userPoolClientId,
      description: "Id of the Cognito App Client for monitoring portal",
    });

    new CfnOutput(this, "AESDomainEndpoint", {
      value: cfnEsDomain.getAtt("DomainEndpoint").toString(),
      description: "Endpoint for the AES Domain",
    });

  }
}
