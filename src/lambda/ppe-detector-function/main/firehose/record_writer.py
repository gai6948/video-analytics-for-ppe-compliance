import boto3
import timeit
import json
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer

logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')

@tracer.capture_method(capture_response=False)
def write_record(record: dict, stream_name: str, firehose_client: None):

    start_time = timeit.default_timer()

    if firehose_client == None:
        firehose_client = boto3.client('firehose')

    payload = json.dumps(record).encode('utf-8')
    
    try:
        firehose_resp = firehose_client.put_record(
            DeliveryStreamName=stream_name,
            Record=payload
        )

        recordId = firehose_resp["RecordId"]
        logger.info(f'Record with id {recordId} put to Firehose after {timeit.default_timer() - start_time}')
    except Exception:
        logger.error('Failed to put record to Firehose')
