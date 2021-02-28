from typing import Tuple
import numpy as np
import imageio
import timeit
import cv2

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')

@tracer.capture_method(capture_response=False)
def decode_frame(raw_frame: bytes, frame_width: int, frame_height: int) -> Tuple[str, np.ndarray]:
    """
    Decode the image bytes into string compatible with OpenCV
    :param raw_frame: frame data in bytes
    :param frame_width width of the frame, obtained from Kinesis payload
    :param frame_height height of the frame, obtained from Kinesis payload
    """

    start_time = timeit.default_timer()
    # frameBuffer = Image.frombytes('RGB', (frame_width, frame_height), raw_frame)
    # frameBuffer.save("./h264decoded.png", "png")
    # frame = np.array(frameBuffer)
    # img_str = cv2.imencode('.jpg', frame)[1].tostring()

    img = imageio.get_reader(raw_frame, ".png")
    frame: np.ndarray = img.get_data(0)
    img_str = cv2.imencode('.png', frame)[1].tostring()

    logger.info(f'Decoded frame after: {timeit.default_timer() - start_time}')
    return img_str, frame
