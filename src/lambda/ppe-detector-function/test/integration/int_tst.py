import os
import cv2

from main.utils.extractor import extract_data
from main.utils.filename_generator import generate_filename
from main.utils.uploader import upload_s3
from main.image_ops.decoder import decode_frame
from main.image_ops.drawer import draw_bounding_box
from main.image_ops.resizer import resize_image
# from main.image_ops.transformer import transform_output
from main.ppedetection.detector import submit_job
from main.ppedetection.filter import filter_result
from main.graphql.mutation import make_mutation
from main.graphql.mutation_preparer import prepare_mutation

# from main.image_ops import decoder, drawer, resizer
# from main.utils import extractor, uploader, filename_generator
# from main.ppedetection import detector, filter
# from main.graphql import mutation, mutation_preparer

def test_integration():

    TARGET_IMAGE_WIDTH = int(os.environ["TARGET_IMAGE_WIDTH"])
    TARGET_IMAGE_HEIGHT = int(os.environ["TARGET_IMAGE_HEIGHT"])

    rek_client = None
    s3_client = None
    min_confidence = int(os.environ["MIN_DETECTION_CONFIDENCE"])
    camera_name = 'test-laptop-01'

    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../data/bytes.txt')
    fp = open(filename, 'rb')
    blob_bytes = fp.read()
    fp.close()

    timestamp, frame_width, frame_height, raw_frame = extract_data(blob_bytes)
    img_str, image = decode_frame(raw_frame, frame_width, frame_height)

    ppe_result = submit_job(img_str, min_confidence, rek_client)
    filtered_resp = filter_result(ppe_result, min_confidence)
    ppl_without_PPE = filtered_resp["Summary"]["SumPeopleWithoutRequiredEquipment"]
    if ppl_without_PPE >= 1:
        for person in filtered_resp["PersonsWithoutRequiredEquipment"]:
            image = draw_bounding_box(person["BoundingBox"], image)
    
    filename = generate_filename(timestamp, camera_name)
    tmp_file = resize_image(image, filename, TARGET_IMAGE_WIDTH, TARGET_IMAGE_HEIGHT)

    upload_s3(tmp_file, ppl_without_PPE, s3_client)
    mutation_req, variables = prepare_mutation(camera_name, filename, timestamp, filtered_resp)
    resp = make_mutation(mutation_req, variables)

    print(resp)
    assert resp["ts"] == '1611502019057'

    # tmp_img = cv2.imread(tmp_file)
    # cv2.imshow('output', tmp_img)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    assert tmp_file == ''

