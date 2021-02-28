import os
import cv2
import json
from PIL import Image

from main.image_ops.cropper import crop_image


def test_crop_image():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/resp.json')
    src_image = os.path.join(src_dirname, '../data/resized-test-img.png')
    src_frame = cv2.imread(src_image)
    with open(src_filename, 'r') as fd:
        res = json.load(fd)
    ppl = res["ppeResult"]["personsWithoutRequiredEquipment"][0]
    new_bytes, new_frame_size = crop_image(src_frame, ppl["boundingBox"])
    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/cropped-img.png')
    # with open(dst_filename, 'wb') as fd:
    #     fd.write(new_bytes)
    new_image = Image.frombytes('RGB', (new_frame_size[1], new_frame_size[0]), new_bytes)
    new_image.save(dst_filename)
    # new_frame = cv2.imread(dst_filename)
    assert len(new_bytes) == 400000
    assert new_frame_size[0] == 397
    assert new_frame_size[1] == 455
