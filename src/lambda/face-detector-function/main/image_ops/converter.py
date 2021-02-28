from typing import Tuple
from PIL import Image
import numpy as np
import timeit
import cv2

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='face-detector', child=True)
tracer = Tracer(service='face-detector')

@tracer.capture_method(capture_response=False)
def convert_frame(old_frame_file: str, format: str) -> str:
    """
    Convert the image to desired format
    :param `old_frame_file`: path to old image file
    :param `format`: desired format ('.png', '.webp', etc)

    :output returns path to new image file
    """    
    old_image = Image.open(old_frame_file)
    new_image = old_image.convert('RGB')
    new_image_path = old_frame_file.split('.')[0] + format
    new_image.save(new_image_path)
    return new_image_path
