import os
import boto3
from main.utils.uploader import upload_s3


def test_upload_s3():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../output/java-frame-decoded-resized.png')
    fd = open(src_filename, 'rb')
    src_bytes = fd.read()
    filename = 'test-upload.png'
    upload_s3(src_bytes, filename, 1, None)
    test_bucket = os.environ["S3_BUCKET"]
    s3_client = boto3.client('s3')
    res = s3_client.get_object(
        Bucket=test_bucket,
        Key=filename
    )
    print(res["ContentLength"])
    assert res["Metadata"]["ppl_without_equipment"] == '1'
