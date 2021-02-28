import os

from main.utils.frame_uploader import upload_frame


BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
key = 'test-laptop-01-2021-01-27-10:54:50:532000.webp'

def test_upload_frame():
    upload_frame(BUCKET_NAME, key, '/tmp/test-laptop-01-2021-01-27-10:54:50:532000.webp', None)
    assert 0 == 1
