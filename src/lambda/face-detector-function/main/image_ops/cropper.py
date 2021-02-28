from typing import Dict, Tuple
import numpy as np
import timeit
from PIL import Image

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='face-detector', child=True)
tracer = Tracer(service='face-detector')

@tracer.capture_method(capture_response=False)
def crop_image(frame: np.ndarray, bounding_box: Dict[str, float]) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Crop an image given a bounding box, encode it as string
    :param `frame`: frame data in numpy array
    :param `bounding_box`: dictionary of the bounding box (width, height, left, top)
    :returns: Tuple of encoded image string and image size (height, width) for cropped image
    """

    start_time = timeit.default_timer()

    img_height, img_width = frame.shape[:2]

    width = int(bounding_box["width"] * img_width)
    height = int(bounding_box["height"] * img_height)
    left = int(bounding_box["left"] * img_width)
    top = int(bounding_box["top"] * img_height)

    if left + width <= img_width:
        right = left + width
    else:
        right = img_width

    if top + height <= img_height:
        bottom = top + height
    else:
        bottom = img_height

    old_frame = Image.fromarray(frame, 'RGB')
    new_frame = np.asarray(old_frame.crop((left, top, right, bottom)))
    new_frame_size = new_frame.shape

    logger.info(f'Resized frame after: {timeit.default_timer() - start_time}')
    return new_frame, new_frame_size
