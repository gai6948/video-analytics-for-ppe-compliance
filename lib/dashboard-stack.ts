import { Construct, Duration, Stack, StackProps } from "@aws-cdk/core";
import * as cw from "@aws-cdk/aws-cloudwatch";
import * as lambda from "@aws-cdk/aws-lambda";
import * as ecs from "@aws-cdk/aws-ecs";
import * as appsync from "@aws-cdk/aws-appsync";
import * as kinesis from "@aws-cdk/aws-kinesis";
import * as logs from "@aws-cdk/aws-logs";

export interface MonitoringDashboardProps extends StackProps {
  ppeDetectorFunction: lambda.Function;
  faceDetectorFunction: lambda.Function;
  ecsCluster: ecs.Cluster;
  fargateAutoScalerFunc: lambda.Function;
  appsyncAPI: appsync.GraphqlApi;
  frameParserLogGroup: logs.LogGroup;
}

export class MonitoringDashboard extends Stack {
  constructor(scope: Construct, id: string, props: MonitoringDashboardProps) {
    super(scope, id, props);

    const ppeDetectorError = new cw.Metric({
      metricName: "Errors",
      namespace: "AWS/Lambda",
      dimensions: {
        FunctionName: props.ppeDetectorFunction.functionName,
      },
      statistic: 'max',
      period: Duration.minutes(1),
    });

    const ppeDetectorInvocation = new cw.Metric({
      metricName: "Invocations",
      namespace: "AWS/Lambda",
      dimensions: {
        FunctionName: props.ppeDetectorFunction.functionName,
      },
      statistic: 'max',
      period: Duration.minutes(1),
    });

    const javaFargateClusterCPUUtil = new cw.Metric({
      metricName: "CpuUtilized",
      namespace: "ECS/ContainerInsights",
      dimensions: {
        // ServiceName: props.javaParserFargateService.serviceName,
        ClusterName: props.ecsCluster.clusterName,
      },
      statistic: 'max',
      period: Duration.minutes(1),
    });

    const javaFargateClusterCPUTotal = new cw.Metric({
      metricName: "CpuReserved",
      namespace: "ECS/ContainerInsights",
      dimensions: {
        // ServiceName: props.javaParserFargateService.serviceName,
        ClusterName: props.ecsCluster.clusterName,
      },
    });

    const javaFargateClusterMemUtil = new cw.Metric({
      metricName: "MemoryUtilized",
      namespace: "ECS/ContainerInsights",
      dimensions: {
        ClusterName: props.ecsCluster.clusterName,
      },
      statistic: 'max',
      period: Duration.minutes(1),
    });

    const javaFargateClusterMemTotal = new cw.Metric({
      metricName: "MemoryReserved",
      namespace: "ECS/ContainerInsights",
      dimensions: {
        ClusterName: props.ecsCluster.clusterName,
      },
    });

    const appSync400Err = new cw.Metric({
      metricName: "4XXError",
      namespace: "AWS/AppSync",
      dimensions: {
        GraphQLAPIId: props.appsyncAPI.apiId,
      },
      statistic: 'max',
      period: Duration.minutes(1),
    });

    const appSync500Err = new cw.Metric({
      metricName: "5XXError",
      namespace: "AWS/AppSync",
      dimensions: {
        GraphQLAPIId: props.appsyncAPI.apiId,
      },
      statistic: 'max',
      period: Duration.minutes(1),
    });

    const rekognitionPPERespTime = new cw.Metric({
      metricName: "ResponseTime",
      namespace: "AWS/Rekognition",
      dimensions: {
        Operation: "DetectProtectiveEquipment",
      },
      statistic: 'max',
      period: Duration.minutes(1),
    });

    // const newFrameStreamIteratorAge = new cw.Metric({
    //   metricName: "GetRecords.IteratorAge",
    //   namespace: "AWS/Kinesis",
    //   dimensions: {
    //     StreamName: props.newFrameStream.streamName
    //   },
    //   statistic: 'max',
    //   period: Duration.minutes(1),      
    // });

    // const newFrameStreamSubscriptionLatency = new cw.Metric({
    //   metricName: "SubscribeToShardEvent.MillisBehindLatest",
    //   namespace: "AWS/Kinesis",
    //   dimensions: {
    //     StreamName: props.newFrameStream.streamName,
    //     ConsumerName: props.newFrameStreamConsumer.attrConsumerName
    //   },
    //   statistic: 'max',
    //   period: Duration.minutes(1),      
    // });

    const fargateAutoScalerError = new cw.Metric({
      metricName: "Errors",
      namespace: "AWS/Lambda",
      dimensions: {
        FunctionName: props.fargateAutoScalerFunc.functionName,
      },
    });

    const fargateAutoScalerInvocation = new cw.Metric({
      metricName: "Invocations",
      namespace: "AWS/Lambda",
      dimensions: {
        FunctionName: props.fargateAutoScalerFunc.functionName,
      },
    });
    
    const faceDetectorError = new cw.Metric({
      metricName: "Errors",
      namespace: "AWS/Lambda",
      dimensions: {
        FunctionName: props.faceDetectorFunction.functionName,
      },
      statistic: 'max',
      period: Duration.minutes(1),      
    });

    const faceDetectorInvocation = new cw.Metric({
      metricName: "Invocations",
      namespace: "AWS/Lambda",
      dimensions: {
        FunctionName: props.faceDetectorFunction.functionName,
      },
      statistic: 'max',
      period: Duration.minutes(1),      
    });
    

    const frameParserErrorFilter = new logs.MetricFilter(this, "FrameParserErrorCount", {
      logGroup: props.frameParserLogGroup,
      filterPattern: {
        logPatternString: "ERROR"
      },
      metricName: "ErrorCount",
      metricNamespace: "KvsFrameParser"
    });

    const frameParserErrorCount = frameParserErrorFilter.metric({
      period: Duration.minutes(1),
      statistic: "max",
    });

    const dashboard = new cw.Dashboard(
      this,
      "VideoMonitoringCloudWatchDashboard-1",
      {}
    );

    dashboard.addWidgets(
      new cw.GraphWidget({
        title: "PPE-Detector-Function-Errors",
        left: [ppeDetectorError],
        right: [ppeDetectorInvocation],
        liveData: true,
        leftYAxis: {
          label: "Errors",
        },
        rightYAxis: {
          label: "Invocations",
        },
      }),
      new cw.GraphWidget({
        title: "AppSync-Error",
        left: [appSync400Err, appSync500Err],
        liveData: true,
        leftYAxis: {
          label: "Error",
        },
      }),
      // new cw.GraphWidget({
      //   title: "Raw-Frame-Stream-Latency",
      //   left: [newFrameStreamIteratorAge, newFrameStreamSubscriptionLatency],
      //   liveData: true,
      //   leftYAxis: {
      //     label: "Miliseconds",
      //   },
      // }),
      new cw.GraphWidget({
        title: "Face-Detector-Function-Errors",
        left: [faceDetectorError],
        right: [faceDetectorInvocation],
        liveData: true,
        leftYAxis: {
          label: "Errors",
        },
        rightYAxis: {
          label: "Invocations",
        },
      }),      
    );

    dashboard.addWidgets(
      new cw.GraphWidget({
        title: "Java-Frame-Parser-Fargate-CPU",
        left: [javaFargateClusterCPUUtil, javaFargateClusterCPUTotal],
        liveData: true,
        leftYAxis: {
          label: "CPU Unit",
        },
      }),
      new cw.GraphWidget({
        title: "Java-Frame-Parser-Fargate-Mem",
        left: [javaFargateClusterMemUtil, javaFargateClusterMemTotal],
        liveData: true,
        leftYAxis: {
          label: "MB",
        },
      }),
      new cw.GraphWidget({
        title: "Rekognition-Response-Time",
        left: [rekognitionPPERespTime],
        liveData: true,
        leftYAxis: {
          label: "ms",
        },
      }),
      new cw.GraphWidget({
        title: "Frame-Parser-Error-Count",
        left: [frameParserErrorCount],
        liveData: true,
        leftYAxis: {
          label: "Error",
        },
      }),
    );

    dashboard.addWidgets(
      new cw.GraphWidget({
        title: "Fargate-AutoScaler-Function-Errors",
        left: [fargateAutoScalerError],
        right: [fargateAutoScalerInvocation],
        liveData: true,
        leftYAxis: {
          label: "Errors",
        },
        rightYAxis: {
          label: "Invocations",
        },
      }),
    );

    // const frameParserErrAlarm = new cw.Alarm(this, "FrameParserErrorAlarm", {
    //   evaluationPeriods: 1,
    //   metric: frameParserErrorCount,
    //   threshold: 5,
    // });

    // frameParserErrAlarm.addAlarmAction();
  }
}
