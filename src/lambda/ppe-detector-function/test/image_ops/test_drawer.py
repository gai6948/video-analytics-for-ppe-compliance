import os
import pytest
import cv2

from main.image_ops.drawer import draw_bounding_box


def test_draw_box():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../output/img_str.txt')
    img = cv2.imread(filename, flags=1)
    test_resp = {
        "Width": 0.7403100728988647,
        "Height": 0.9412225484848022,
        "Left": 0.02214839495718479,
        "Top": 0.03134796395897865
    }
    new_img = draw_bounding_box(test_resp, img)
    cv2.imshow('showtest', new_img)
    assert len(new_img.shape) ==3
