from datetime import datetime, timedelta
import os
import boto3

ecs = boto3.client('ecs')
cw = boto3.client('cloudwatch')
kvs = boto3.client('kinesisvideo')
ddb = boto3.client('dynamodb')

fargate_cluster_name = os.environ["FARGATE_CLUSTER_NAME"]
fargate_task_def_arn = os.environ["TASK_DEF_ARN"]
subnet1 = os.environ["SUBNET_ONE"]
subnet2 = os.environ["SUBNET_TWO"]
ddb_table = os.environ["TASK_MAPPING_TABLE"]


def list_kvs_streams():
    kvs_resp = kvs.list_streams()
    return kvs_resp["StreamInfoList"]


def check_task_mapping(camera_id):
    task_mapping_resp: dict = ddb.get_item(
        TableName=ddb_table,
        Key={
            'cameraId': {
                'S': camera_id
            }
        }
    )
    if 'Item' in task_mapping_resp:
        currentWorker = task_mapping_resp['Item']['currentWorker']['S']
    else:
        return 'NoWorker'
    return currentWorker


def update_task_mapping(camera_id, task_id):
    ddb.put_item(
        TableName=ddb_table,
        Item={
            'cameraId': {
                'S': camera_id
            },
            'currentWorker': {
                'S': task_id
            }
        }
    )


# def list_ecs_task():
#     task_status_resp = ecs.list_tasks(
#         cluster=fargate_cluster_name,
#         desiredStatus='RUNNING',
#         launchType='FARGATE'
#     )
#     return task_status_resp['taskArns']


def start_ecs_task():
    start_task_resp = ecs.run_task(
        launchType='FARGATE',
        count=1,
        cluster=fargate_cluster_name,
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': [
                    subnet1,
                    subnet2,
                ]
            }
        },
        taskDefinition=fargate_task_def_arn
    )

    task_status = start_task_resp["tasks"][0]["lastStatus"]
    if task_status == 'PENDING' or 'PROVISIONING':
        print("Launched 1 fargate task")
        return start_task_resp["tasks"][0]["taskArn"]
    else:
        print(f"Launch task failed, current task state: {task_status}")


def stop_ecs_task(task_arn):
    stop_task_response = ecs.stop_task(
        cluster=fargate_cluster_name,
        task=task_arn,
        reason='AutoScaling Scale In'
    )
    desired_status = stop_task_response["task"]["desiredStatus"]
    if desired_status == "STOPPED":
        print("Stopped 1 fargate task...")
    else:
        print(f"Stop task failed, desired task status: {desired_status}")


def check_kvs_metric(stream_name):
    producerByteCount = None
    consumerByteCount = None
    three_min_ago = datetime.utcnow() - timedelta(minutes=2)
    one_min_ago = datetime.utcnow() - timedelta(minutes=1)
    cw_response = cw.get_metric_data(
        MetricDataQueries=[
            {
                'Id': 'kvsProducerByte',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/KinesisVideo',
                        'MetricName': 'PutMedia.IncomingBytes',
                        'Dimensions': [
                            {
                                'Name': 'StreamName',
                                'Value': stream_name
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Minimum',
                    'Unit': 'Bytes'
                },
                'Label': 'KvsProducerByte',
                'ReturnData': True,
                # 'Period': 60
            },
            {
                'Id': 'kvsConsumerByte',
                'MetricStat': {
                    'Metric': {
                        'Namespace': 'AWS/KinesisVideo',
                        'MetricName': 'GetMedia.OutgoingBytes',
                        'Dimensions': [
                            {
                                'Name': 'StreamName',
                                'Value': stream_name
                            },
                        ]
                    },
                    'Period': 60,
                    'Stat': 'Minimum',
                    'Unit': 'Bytes'
                },
                'Label': 'KvsConsumerByte',
                'ReturnData': True,
                # 'Period': 60
            },
        ],
        StartTime=three_min_ago,
        EndTime=one_min_ago,
        ScanBy='TimestampDescending',
        MaxDatapoints=3
    )

    if len(cw_response["Messages"]) != 0:
        cwStatusCode = cw_response["Messages"][0]["Code"]
        cwErrMsg = cw_response["Messages"][0]["Value"]
        if cwStatusCode != "200":
            raise(f"CloudWatch Error: {cwErrMsg}")

    for metric in cw_response["MetricDataResults"]:
        if metric["Id"] == 'kvsProducerByte':
            if metric["StatusCode"] != "InternalError":
                if len(metric["Values"]) == 0:
                    producerByteCount = 0
                else:
                    producerByteCount = metric["Values"][0]
                print(f"KVS Producer Byte Count: {producerByteCount} for stream {stream_name}")
            else:
                cwErrMsg = metric["Messages"][0]["Value"]
                raise(f"CloudWatch Error: {cwErrMsg}")
        if metric["Id"] == 'kvsConsumerByte':
            if metric["StatusCode"] != "InternalError":
                if len(metric["Values"]) == 0:
                    consumerByteCount = 0
                else:
                    consumerByteCount = metric["Values"][0]
                print(f"KVS Consumer Byte Count: {consumerByteCount} for stream {stream_name}")
            else:
                cwErrMsg = metric["Messages"][0]["Value"]
                raise(f"CloudWatch Error: {cwErrMsg}")
    return producerByteCount, consumerByteCount


def handler(event, context):
    if subnet1 == '' or subnet2 == '':
        raise Exception("Not enough subnets specified, exiting")
    for kvs_stream in list_kvs_streams():
        stream_name = kvs_stream["StreamName"]
        producerByteCount, consumerByteCount = check_kvs_metric(
            stream_name)
        if producerByteCount is not None and consumerByteCount is not None:
            ## Start Fargate task if there is video in and no worker present
            if producerByteCount > 0 and consumerByteCount == 0:
                current_worker = check_task_mapping(stream_name)
                if current_worker == "NoWorker":
                    current_worker = start_ecs_task()
                    update_task_mapping(stream_name, current_worker)
            ## Stop corresponding Fargate task if no video in
            if producerByteCount == 0:
                current_worker = check_task_mapping(stream_name)
                if current_worker != "NoWorker":
                    stop_ecs_task(current_worker)
                    update_task_mapping(stream_name, "NoWorker")
        else:
            raise("Error comparing metrics")
