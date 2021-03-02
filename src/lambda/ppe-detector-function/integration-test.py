import os
import json
from typing import Any, Dict
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from main.image_ops import decoder, drawer, resizer
from main.utils import uploader, filename_generator, frame_downloader
from main.ppedetection import detector, filter, notifier
from main.graphql import mutation, mutation_preparer
from index import handler

TARGET_IMAGE_WIDTH = int(os.environ["TARGET_IMAGE_WIDTH"])
TARGET_IMAGE_HEIGHT = int(os.environ["TARGET_IMAGE_HEIGHT"])
MIN_CONFIDENCE = int(os.environ["MIN_DETECTION_CONFIDENCE"])
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

rek_client = None
s3_client = None

logger = Logger(service='ppe-detector', level='INFO')
tracer = Tracer(service='ppe-detector')

f = open("./test/data/event.json")
src = json.load(f)
handler(src, None)
