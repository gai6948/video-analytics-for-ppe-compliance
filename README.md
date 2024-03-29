# Real-time Video Analytics for PPE Compliance

For many enterprises, petabytes of data are generated from their CCTV everyday, however they are often untapped. Facial Rekognition, social distancing measurement, protective equipment detection, or accident prevention are just examples of common use cases of real-time video analytics. With [Amazon Rekognition](https://aws.amazon.com/rekognition/), you can obtain insights from video without ML knowledge, and with slightly more efforts, [Amazon Sagemaker](https://aws.amazon.com/sagemaker/) can be used to deploy ML model for advanced use cases.

This solution demonstrates streaming videos from cameras of any kind to AWS for real-time analytics on PPE compliance, using Amazon Rekognition, and visualize such data in a dashboard and a monitoring portal. While this example mainly focus on PPE compliance, the general architecture can be applied for other use cases as well (i.e. intrusion detection, people tracking/counting, etc)

<p align="center">
  <a href="#architecture">Architecture</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#customizing the solution">Customizing the solution</a> •
</p>

## Architecture

<img src="doc/arch1.png" />

The solution is comprised of different parts, and can be broken down into the following sections:

* <b>[Video Injestion](#video-injestion) </b>
* <b>[Raw video Processing](#raw-video-processing) </b>
* <b>[Inference Pipeline](#inference-pipeline) </b>
* <b>[Alerting and result presentation](#alerting-and-result-presentation) </b>
* <b>[Analytics Dashboard](#analytics-dashboard) </b>

### Video Injestion

The injestion of video is done via Kinesis Video Streams (KVS), it enables video producers of any kind (ip cameras, CCTV, Raspberry Pi, or even your laptop) to efficiently transfer video data to the cloud securely. 

 > The recommended way to use KVS is via the [GStreamer plugin](https://docs.aws.amazon.com/kinesisvideostreams/latest/dg/examples-gstreamer-plugin.html). While GStreamer is an application that is considered too heavy to install in a typical embedded device, for prototyping or architectures that can leverage an edge video gateway (aggregating cameras from different sources), using Gstreamer abstracts you away from many video encoding/transmuxing details and Gstreamer is extensible to other plugins, like applying ML filter before sending videos to KVS, or integrate with [Nvidia DeepStream SDK](https://developer.nvidia.com/deepstream-sdk)

### Raw Video Processing

The architecture for raw video processing is inspired from the Proserv team's brilliant [blog post](https://aws.amazon.com/blogs/machine-learning/accelerating-the-deployment-of-ppe-detection-solution-to-comply-with-safety-guidelines/), where they introduced a scalable pattern for processing KVS video streams using a fleet of auto-scaling Fargate tasks (Using the [KVS Parser Library](https://github.com/aws/amazon-kinesis-video-streams-parser-library) in Java), scaled using KVS producer and consumer metrics, when there is no video in, consuming task can be shut down, and when video is coming in, a task is spawned to consume on the video stream. The only difference betweeen the implementation is that here the DynamoDB table only stores which Fargate task is consuming which video stream, and no checkpointing logic is implemented.

<img src="doc/blog-vidin.jpg" />

### Inference Pipeline

The inference pipeline consists of a few steps, when video frame is uploaded in the raw frame bucket, an S3 event is triggered, going through SNS to SQS, picked up by a Lambda worker to do PPE Analysis using Rekognition's PPE API. The reason for this design is due to Rekognition PPE's API hard limit of 5 concurrent invocation per account/region, so the concurrency of the Lambda must be controlled at a maximum of 5, regardless of how many video streams. Prior and after calling the Rekognition PPE API, there are some image resizing and format conversion done by the Lambda, processed images are stored in a destination bucket in webp format, which greatly reduces image size (3xxKB -> 2xKB). For each processed frames, the result are persisted in an ElasticSearch domain for analytics (to be explained [later](#analytics-dashboard))

For SageMaker-based inference solutions, the architecture can be simplified by having the KVS Consumer Fargate task directly invoking the Sagemaker endpoint, saving a lot of load-levelling resources.

<img src="doc/inf-pipeline.png" />

### Alerting and result presentation

If Rekognition PPE detects violation case, an SNS notification is sent to a downstream Lambda. The Lambda function will perform a face search against stored faces, to identify the person without PPE. After the bounding boxes are drawn, an alert is sent to an AppSync API, after which to be stored in a DynamoDB table. From the monitoring portal (a custom Web UI), users can see a list of alerts with number of PPE violation in each of them, and also the image.

<img src="doc/portal-ui.png" />

### Analytics Dashboard

Kibana dashboard is used for visualizing the PPE violation data over a time-series. Key metrics that can be created include number of violations in a given time period, person/camera with most violations, etc.

## Deployment

This solution was developed by AWS CDK, and deployment is done through CodePipeline, otherwise the deployment can slow up your machine and takes a lot of time.

### Prequisites

First make sure you have installed [AWS CDK](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) and have Node.JS v10 or above. You should also have [jq](https://stedolan.github.io/jq/) installed. You should also have [SSH key set up for CodeCommit](https://docs.aws.amazon.com/codecommit/latest/userguide/setting-up-ssh-unixes.html)

### Deploy the CDK Pipeline

As the first step we will deploy the CDK pipeline. Region is assumed to be us-west-2, but you can change that in `bin/cdk.ts`

```
npm install
npx cdk deploy --require-approval never --json true -O pipeline-output.json
```

Wait for the deployment to finish, then we will deploy the remaining stuffs.

After the deployment completes, we will add the cretaed CodeCommit repository as our remote repo:
```
codecommiturl=$(jq -r '.VideoAnalyticsPipelineStack.CodeCommitRepoSshUrl' pipeline-output.json)
git remote add codecommit $codecommiturl
```

### Deploy the solution

Now we can deploy the resources that powers our solution.

First we will uncomment the deployment stage of our pipeline:
`sed -i .bak 's|// ||' lib/pipeline-stack.ts`

And then we will push the code to the remote repo so it is automatically deployed
```
git add .
git commit -m "Initial Commit"
git push -u codecommit master
```

The deployment should take around 30 minutes, you can take a break first.

### See deployment results

Once the deployment is ready, you should see some stacks in your [CloudFormation console](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/)

## Add face collection (Optional)

If you want to display face-id on PPE violation, you can add a face collection in Amazon Rekognition, so that you can differentiate between different people, for details on how to add a face collection, visit the [documentation](https://docs.aws.amazon.com/rekognition/latest/dg/create-collection-procedure.html). Once the face collection is created, change line 186 of `lib/frame-processor-stack.ts` to modify the Lambda environment variable (FACE_COLLECTION_ID) to point to your face collection.

Web UI for adding face collection using browser webcam is currently on the backlog.

## Customizing the solution

### Customizing the KVS Consumer

In order to reduce deployment time (otherwise 1 more hour of maven build), the container image for KVS Consumer (Frame Parser) is pre-built, and on deployment time it pulls from my ECR public gallery, you can modify the CDK code in `lib/frame-parser-stack.ts` to use the folder in `src/ecs/kvs-frame-parser`

## Backlog

* Web UI for creating Rekognition face collection using browser webcam
* Fix bounding box dislocation in face detector Lambda
* Alarm deduplication in case of same person appearing in consecutive alarms
* Custom ML model instead of Rekognition PPE API

