import { Construct, Stack, StackProps } from "@aws-cdk/core";
import * as ec2 from "@aws-cdk/aws-ec2";
import * as ecs from "@aws-cdk/aws-ecs";


export interface SharedInfraStackProps extends StackProps {
}

// Stack conataining shared resources like VPC and Lambda layers shared across different functions
export class SharedInfraStack extends Stack {
  public readonly vpc: ec2.Vpc;
  public readonly cluster: ecs.Cluster;
  public readonly privateSubnets: ec2.SubnetSelection;

  constructor(scope: Construct, id: string, props?: SharedInfraStackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, "VideoMonitoringVPC", {
      cidr: "10.0.0.0/16",
      maxAzs: 2,
      subnetConfiguration: [
        {
          name: "public-sn",
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: "private-sn",
          subnetType: ec2.SubnetType.PRIVATE,
          cidrMask: 24,
        },
      ],
      enableDnsHostnames: true,
      enableDnsSupport: true,
    });

    this.vpc = vpc;

    const cluster = new ecs.Cluster(this, "VideoMonitoringFargateCluster", {
      clusterName: "VideoMonitoringFargateCluster",
      containerInsights: true,
      vpc: this.vpc,
    });
    this.cluster = cluster;

    // Export private subnets used for launching Fargate tasks
    const privateSubnets = this.vpc.selectSubnets({
      subnetType: ec2.SubnetType.PRIVATE,
    });
    this.privateSubnets = privateSubnets;

    // Create Kinesis Streams interface endpoint for all private subnet
    vpc.addInterfaceEndpoint("kinesis-endpoint", {
      service: ec2.InterfaceVpcEndpointAwsService.KINESIS_STREAMS,
      open: true,
      privateDnsEnabled: true,
      subnets: this.privateSubnets,
    });

    // Create S3 Gateway Endpoint for future use
    vpc.addGatewayEndpoint("s3-gw-endpoint", {
      service: ec2.GatewayVpcEndpointAwsService.S3,
      subnets: [{ subnetType: ec2.SubnetType.PRIVATE }],
    });


  }
}
