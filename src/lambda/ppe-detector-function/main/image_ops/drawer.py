import timeit
import cv2
import numpy as np

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')

# Draw bounding box on the frame based on a bounding box coordinates
@tracer.capture_method(capture_response=False)
def draw_bounding_box(box_coordinates: dict, frame: np.ndarray) -> np.ndarray:
    """
    Draw bounding box on the frame based on a bounding box coordinates
    """

    start_time = timeit.default_timer()
    label_left = box_coordinates["Left"]
    label_top = box_coordinates["Top"]
    if label_left > 0.0 and label_left < 1.0: # Ignore drawing if the bounding box is outside of frame
        if label_top > 0.0 and label_top < 1.0:
            height, width = frame.shape[:2]
            label_height = box_coordinates["Height"]
            label_width = box_coordinates["Width"]
            x1 = int(label_left * width)
            y1 = int(label_top * height)
            x2 = int(x1 + label_width * width)
            y2 = int(y1 + label_height * height)
            # Using red as the color of the bounding box here
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 5)
    logger.info(
        f'Image drawing completed after: {timeit.default_timer() - start_time}')
    return frame
