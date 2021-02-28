import os
import cv2
import json
from PIL import Image

from main.facedetection.detector import submit_job

FACE_SEARCH_MIN_CONFIDENCE = int(os.environ["FACE_SEARCH_MIN_CONFIDENCE"])
FACE_COLLECTION_ID = os.environ["REKOGNITION_FACE_COLL_ID"]

def test_submit_job():
    src_dirname = os.path.dirname(__file__)
    src_filepath = os.path.join(src_dirname, '../output/cropped-img.png')
    with open(src_filepath, 'rb') as fd:
        src_image_bytes = fd.read()
    # src_image = Image.open(src_filepath)
    # src_bytes = src_image.tobytes()
    resp = submit_job(src_image_bytes, FACE_SEARCH_MIN_CONFIDENCE, None, FACE_COLLECTION_ID)
    dst_dirname = os.path.dirname(__file__)
    dst_filepath = os.path.join(dst_dirname, '../output/face-res.json')
    with open(dst_filepath, 'w') as fd:
        json.dump(resp, fd)
    assert len(resp["FaceMatches"]) >= 1
