import numpy as np
import timeit
import cv2
from PIL import Image

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')

@tracer.capture_method(capture_response=False)
def resize_image(frame: np.ndarray, filename: str, target_image_width: int, target_image_height: int) -> str:
    """
    Resize the drawn image and save to /tmp directory before uploading to S3
    :param `frame`: frame data in numpy array
    """

    start_time = timeit.default_timer()
    new_frame: np.ndarray = cv2.resize(frame, dsize=(target_image_width, target_image_height), interpolation=cv2.INTER_LINEAR)
    tmp_filename = f'/tmp/{filename}'
    img = Image.fromarray(new_frame)
    img.save(tmp_filename, 'webp')
    # cv2.imwrite(tmp_filename, new_frame)
    # image_bytes: bytes = new_frame.tobytes()
    logger.info(f'Resized frame after: {timeit.default_timer() - start_time}')
    return tmp_filename

