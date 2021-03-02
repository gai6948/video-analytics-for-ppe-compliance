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

TARGET_IMAGE_WIDTH = int(os.environ["TARGET_IMAGE_WIDTH"])
TARGET_IMAGE_HEIGHT = int(os.environ["TARGET_IMAGE_HEIGHT"])
MIN_CONFIDENCE = int(os.environ["MIN_DETECTION_CONFIDENCE"])
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

rek_client = None
s3_client = None

logger = Logger(service='ppe-detector', level='INFO')
tracer = Tracer(service='ppe-detector')

@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext):
    for record in event["Records"]:
        logger.info(record)
        rec = json.loads(record["body"])
        for s3e in rec["Message"]["Records"]:
            src_s3bucket = s3e["s3"]["bucket"]["body"]["name"]
            src_s3key = s3e["s3"]["object"]["key"]
            frame_bytes, metadata = frame_downloader.download_frame(src_s3bucket, src_s3key, s3_client)
            camera_name = src_s3key.split("/")[0]
            timestamp = metadata["timestamp"]
            frame_width = int(metadata["frame-width"])
            frame_height = int(metadata["frame-height"])
            img_str, image = decoder.decode_frame(frame_bytes, frame_width, frame_height)
            ppe_result = detector.submit_job(img_str, MIN_CONFIDENCE, rek_client)
            filtered_resp = filter.filter_result(ppe_result, MIN_CONFIDENCE)
            ppl_without_PPE = filtered_resp["Summary"]["SumPeopleWithoutRequiredEquipment"]
            if ppl_without_PPE >= 1:
                for person in filtered_resp["PersonsWithoutRequiredEquipment"]:
                    image = drawer.draw_bounding_box(person["BoundingBox"], image)
            filename = filename_generator.generate_filename(timestamp, camera_name)
            tmp_file = resizer.resize_image(image, filename, TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT)
            uploader.upload_s3(tmp_file, ppl_without_PPE, s3_client)
            mutation_req, variables = mutation_preparer.prepare_mutation(camera_name, filename, timestamp, filtered_resp)
            resp = mutation.make_mutation(mutation_req, variables)
            if ppl_without_PPE >= 1:
                sns_status = notifier.notify_alarm(SNS_TOPIC_ARN, variables)
    return {
        "statusCode": 200,
        "body": {"processed": "true"}
    }
