import cv2
from main.image_ops.drawer import draw_bounding_box
from main.facedetection.detector import submit_job
from PIL import Image
import os
import numpy as np

def test_uncropped_drawer():
    src_dirname = os.path.dirname(__file__)
    src_image_path = os.path.join(src_dirname, '../data/resized-test-img.png')

    with open(src_image_path, 'rb') as fp:
        src_frame_bytes = fp.read()

    face_res = submit_job(src_frame_bytes, 80, None, 'test-collection-01')
    face_res_list = [face_res]
    print(face_res)

    sub_frame_size_list=[(480, 640)]

    # resized_src_frame = Image.frombytes('RGB', (640, 480), src_frame_bytes)
    resized_src_frame = np.asarray(Image.open(src_image_path))

    output_frame = draw_bounding_box(face_res_list, sub_frame_size_list, resized_src_frame)

    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/drawn-uncropped-img.png')
    cv2.imwrite(dst_filename, output_frame)

    assert 0 == 1
