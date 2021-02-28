# Submit detection job to Rekognition PPE
import timeit
import boto3

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')

@tracer.capture_method(capture_response=False)
def submit_job(img_str: str, min_confidence: int, rek_client: None) -> dict:
    start_time = timeit.default_timer()

    if not rek_client:
        rek_client = boto3.client("rekognition")

    ppe_response = rek_client.detect_protective_equipment(
        Image={
            'Bytes': img_str,
        },
        SummarizationAttributes={  # Detect whether workers have weared helmet and mask
            'MinConfidence': min_confidence,
            'RequiredEquipmentTypes': [
                'FACE_COVER',
                'HEAD_COVER'
            ]
        }
    )

    logger.info(
        f'Rekognition PPE detection completed after: {timeit.default_timer() - start_time}')
        
    return ppe_response
