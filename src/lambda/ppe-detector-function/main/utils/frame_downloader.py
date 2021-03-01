from typing import Any, Tuple, Dict
import boto3
import timeit

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer

logger = Logger(service='face-detector', child=True)
tracer = Tracer(service='face-detector')


@tracer.capture_method(capture_response=False)
def download_frame(bucket_name: str, key: str, s3_client: None) -> Tuple[bytes, Dict[str, str]]:

    start_time = timeit.default_timer()
    if s3_client == None:
        s3_client = boto3.client('s3')

    try:
        resp = s3_client.get_object(
            Bucket=bucket_name,
            Key=key
        )
        frame_data = resp["Body"].read()
        metadata = resp["Metadata"]
        logger.info(
            f'Frame downloaded from S3 completed after: {timeit.default_timer() - start_time}') 
        return frame_data, metadata
    except(Exception):
        logger.exception("Error downloading frame from S3")
