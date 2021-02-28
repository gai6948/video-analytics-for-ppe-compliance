import os

from main.utils.frame_downloader import download_frame


BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
key = 'test-laptop-01-2021-01-27-10:54:50:532000.webp'

def test_download_frame():
    tmp_filename = download_frame(BUCKET_NAME, key, None)
    assert tmp_filename == '/tmp/test-laptop-01-2021-01-27-10:54:50:532000.webp'
