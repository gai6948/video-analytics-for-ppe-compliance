import timeit
import boto3
import botocore
import os

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')


# Upload image to s3, with number of people detected without PPE as metadata
@tracer.capture_method(capture_response=False)
def upload_s3(tmp_filename: str, ppl_without_equipment: int, s3_client: None) -> None:
    """
    Upload image to S3
    :param `frame` bytes of the frame
    :param `camera_name` S3 key of the frame
    :param `ppl_without_equipment` number of people without protective equipment, attached as object metadata
    :param `s3_client` please input None
    """

    start_time = timeit.default_timer()
    try:
        if not s3_client:
            s3_client = boto3.client("s3")

        s3_res = s3_client.upload_file(
            Filename=tmp_filename,
            Bucket=os.environ["PROCESSED_S3_BUCKET"],
            Key=tmp_filename[5:],
            ExtraArgs={
                "Metadata": {
                    "ppl_without_equipment": str(ppl_without_equipment)
                },
                "ContentType": "image/webp",
                "ServerSideEncryption": "AES256"
            }
        )

        logger.info(
            tmp_filename[5:] + f' uploaded to S3 after {timeit.default_timer() - start_time}')
    except botocore.exceptions.ClientError as error:
        logger.exception('Error occured when uploading to S3: ' + error)
