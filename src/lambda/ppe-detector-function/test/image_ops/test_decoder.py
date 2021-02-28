import os
import pytest
import cv2

from main.image_ops.decoder import decode_frame

# @pytest.mark.run(order=2)
def test_decode():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/java-frame.png')
    src_file = open(src_filename, 'rb')
    frameData = src_file.read()
    src_file.close()
    img_str, frame = decode_frame(frameData, 640, 480)
    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/java-frame-decoded.png')
    cv2.imwrite(dst_filename, frame)
    

    assert len(frame.shape) == 3
