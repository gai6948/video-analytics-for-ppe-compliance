from datetime import datetime
import timeit
import cv2
import numpy as np

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')

# Transform the frame into jpg file before storing to S3
@tracer.capture_method(capture_response=False)
def transform_output(frame: np.ndarray, timestamp: str, camera_name: str) -> str:
    start_time = timeit.default_timer()
    timestr = str(datetime.fromtimestamp(int(timestamp)/1000)).replace(' ', '-')
    filename = '/tmp/' + camera_name + '-' + timestr + '.jpg'
    cv2.imwrite(filename, frame)
    logger.info(
        f'Image transformation completed after: {timeit.default_timer() - start_time}')
    return filename
