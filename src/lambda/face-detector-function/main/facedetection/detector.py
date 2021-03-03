# Submit detection job to Rekognition Face Detection
import timeit
import boto3

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
import cv2
from numpy import ndarray


logger = Logger(service='face-detector', child=True)
tracer = Tracer(service='face-detector')

@tracer.capture_method(capture_response=False)
def submit_job(img: ndarray, min_confidence: int, rek_client: None, face_collection) -> dict:
    start_time = timeit.default_timer()
    img_str = cv2.imencode('.png', img)[1].tostring()
    if not rek_client:
        rek_client = boto3.client("rekognition")

    try:
        face_res = rek_client.search_faces_by_image(
            CollectionId=face_collection,
            Image={
                'Bytes': img_str
            },
            MaxFaces=1,
            FaceMatchThreshold=float(min_confidence/100)
        )
    except rek_client.exceptions.InvalidParameterException as e:
        logger.warn("No faces detected in image")
        return None
    logger.info(
        f'Rekognition face search completed after: {timeit.default_timer() - start_time}')
        
    return face_res
