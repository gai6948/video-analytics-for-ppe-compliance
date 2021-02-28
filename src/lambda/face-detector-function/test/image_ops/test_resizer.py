import os
import cv2

from main.image_ops.resizer import resize_image

SOURCE_IMAGE_WIDTH = 640
SOURCE_IMAGE_HEIGHT = 480

def test_resizer():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/test-laptop-01-2021-01-27-10:54:50:532000.png')
    src_img = cv2.imread(src_filename)
    output_img = resize_image(src_img, SOURCE_IMAGE_WIDTH, SOURCE_IMAGE_HEIGHT)
    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/resized-test-img.png')
    cv2.imwrite(dst_filename, output_img)
