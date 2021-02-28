import boto3
import timeit
import io

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='face-detector', child=True)
tracer = Tracer(service='face-detector')

@tracer.capture_method(capture_response=False)
def upload_frame(bucket_name: str, key: str, filepath: str, s3_client: None):
    start_time = timeit.default_timer()

    if s3_client == None:
        s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(filepath, bucket_name, key)
        logger.info(
            f'Frame uploaded to S3 after: {timeit.default_timer() - start_time}') 
    except Exception:
        logger.exception("Error uploading frame to S3")
