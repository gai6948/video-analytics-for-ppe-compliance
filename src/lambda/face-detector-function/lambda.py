import json
import os
import cv2
from typing import Any, Dict

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from main.utils import frame_downloader, frame_uploader
from main.image_ops import converter, resizer, cropper, drawer
from main.facedetection import detector
from main.graphql import mutation_preparer, mutation_executor

FRAME_BUCKET_NAME = os.environ["FRAME_BUCKET_NAME"]
GRAPHQL_API_ENDPOINT = os.environ["GRAPHQL_API_ENDPOINT"]
FACE_COLLECTION_ID = os.environ["FACE_COLLECTION_ID"]
MIN_CONFIDENCE_THRESHOLD = int(os.environ["MIN_CONFIDENCE_THRESHOLD"])

SOURCE_IMAGE_WIDTH = 640
SOURCE_IMAGE_HEIGHT = 480

rek_client = None
s3_client = None

logger = Logger(service='face-detector', level='INFO')
tracer = Tracer(service='face-detector')

@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext):
    for record in event['Records']:
        message = record["Sns"]["Message"]
        print(message)
        msg = json.loads(message)
        if msg["ppeViolationCount"] != 0:
            old_frame_key = msg["s3url"].split('/')[1]
            old_frame_filepath, s3_client = frame_downloader.download_frame(FRAME_BUCKET_NAME, old_frame_key, None)
            converted_frame_filepath = converter.convert_frame(old_frame_filepath, '.png')
            converted_src_frame = cv2.imread(converted_frame_filepath)
            resized_src_frame = resizer.resize_image(converted_src_frame, SOURCE_IMAGE_WIDTH, SOURCE_IMAGE_HEIGHT)
            resp_list = []
            sub_frame_size_list = []
            for ppl in msg["ppeResult"]["personsWithoutRequiredEquipment"]:
                sub_image, sub_frame_size = cropper.crop_image(resized_src_frame, ppl["boundingBox"])
                sub_frame_size_list.append(sub_frame_size)
                face_detection_res = detector.submit_job(sub_image, MIN_CONFIDENCE_THRESHOLD, rek_client, FACE_COLLECTION_ID)
                resp_list.append(face_detection_res)
            drawn_frame_path = '/tmp/' + old_frame_key.split('.')[0] + '.png'
            drawer.draw_bounding_box(resp_list, sub_frame_size_list, resized_src_frame, drawn_frame_path)
            output_frame_filepath = converter.convert_frame(drawn_frame_path, '.webp')
            frame_uploader.upload_frame(FRAME_BUCKET_NAME, old_frame_key, output_frame_filepath, s3_client)
            mutation, variables = mutation_preparer.prepare_mutation(msg, resp_list)
            mutation_executor.make_mutation(mutation, variables, GRAPHQL_API_ENDPOINT)
        else:
            logger.info("No PPE violation in alert, exiting...")
        