import boto3
import json

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')
@tracer.capture_method(capture_response=False)
def notify_alarm(topic_arn, result):
    sns_client = boto3.client('sns')
    try:
        sns_res = sns_client.publish(
            TopicArn=topic_arn,
            Message=json.dumps(result)
        )
        logger.info(f'Message sent to topic with mesasge ID {sns_res["MessageId"]}.')
        return True
    except Exception:
        logger.exception("Error sending alarm to SNS")
        return False
