import cv2
from main.image_ops.drawer import draw_bounding_box
import os
import json


def test_drawer():
    src_dirname = os.path.dirname(__file__)

    src_filename = os.path.join(src_dirname, '../data/face-res.json')
    with open(src_filename, 'r') as fd:
        res = json.load(fd)
    resp_list = [res]
    sub_frame_size_list = [(397, 455)]

    src_image = os.path.join(src_dirname, '../data/resized-test-img.png')
    resized_src_frame = cv2.imread(src_image)

    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/drawn-img.png')
    draw_bounding_box(resp_list, sub_frame_size_list, resized_src_frame, dst_filename)

    # cv2.imwrite(dst_filename, output_frame)

    assert 0 == 1
    