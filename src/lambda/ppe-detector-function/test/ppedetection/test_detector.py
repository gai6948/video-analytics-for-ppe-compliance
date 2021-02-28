import os
import cv2
import json
# import pytest

from main.ppedetection.detector import submit_job

# @pytest.mark.run(order=3)
def test_detect():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/java-frame.png')
    img = cv2.imread(src_filename, flags=1)
    img_str = cv2.imencode('.png', img)[1].tostring()
    ppe_result = submit_job(img_str, 70, None)
    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/ppe-result-java-frame.json')
    with open(dst_filename, 'w') as fd:
        json.dump(ppe_result,fd)

    assert len(ppe_result["Summary"]["PersonsWithRequiredEquipment"]) == 0
    assert len(ppe_result["Summary"]["PersonsWithoutRequiredEquipment"]) == 1
