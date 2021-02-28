import cv2
import os
from PIL import Image 
import numpy as np

from main.image_ops.resizer import resize_image


def test_resize_image():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../output/java-frame-decoded.png')
    img = cv2.imread(src_filename, flags=1)
    target_width = 320
    target_height = 480
    new_img_path = resize_image(img, 'converted-image.webp', target_height, target_width)
    # frame = np.frombuffer(new_image_bytes, dtype=img.dtype)
    # frameBuffer = Image.frombytes('RGB', (target_height, target_width), new_image_bytes)
    frameBuffer = Image.open(new_img_path)
    frameArray = np.array(frameBuffer)
    height, width, channel = frameArray.shape
    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/java-frame-decoded-resized.webp')
    cv2.imwrite(dst_filename, frameArray)
    assert width == 480
    assert height == 320
    # fd = open(dst_filename, 'wb')
    # fd.write(new_image_bytes)
    # fd.close()
