import os
import boto3
import pytest

from main.utils.extractor import extract_data

# @pytest.mark.run(order=1)
def test_extract_data():
    dirname = os.path.dirname(__file__)
    filename = os.path.join(dirname, '../data/bytes.txt')
    fp = open(filename, 'rb')
    blob_bytes = fp.read()
    timestamp, frame_width, frame_height, raw_frame = extract_data(blob_bytes)
    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/java-frame.png')
    dst_fp = open(dst_filename, 'wb')
    dst_fp.write(raw_frame)
    dst_fp.close()
    print(timestamp)
    print(frame_width)
    print(frame_height)
    assert frame_width == 640
    assert frame_height ==480
