import json
import os
from index import handler 

FRAME_BUCKET_NAME = os.environ["FRAME_BUCKET_NAME"]
GRAPHQL_API_ENDPOINT = os.environ["GRAPHQL_API_ENDPOINT"]
FACE_COLLECTION_ID = os.environ["FACE_COLLECTION_ID"]
MIN_CONFIDENCE_THRESHOLD = int(os.environ["MIN_CONFIDENCE_THRESHOLD"])

SOURCE_IMAGE_WIDTH = 640
SOURCE_IMAGE_HEIGHT = 480

rek_client = None
s3_client = None

dst_dirname = './test/data'
dst_filepath = os.path.join(dst_dirname, 'resp.json')
with open(dst_filepath, 'r') as fd:
    msg = json.load(fd)
    ev = json.dumps(msg)
handler(ev, '')
