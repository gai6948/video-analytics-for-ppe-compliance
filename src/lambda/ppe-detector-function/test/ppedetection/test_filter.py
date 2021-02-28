import json
import os
from main.ppedetection.filter import filter_result


def test_filter_result():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/ppe-result.json')
    with open(src_filename, 'r') as fd:
        ppe_res = json.load(fd)
    filtered_res = filter_result(ppe_res, 70)
    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/filtered-ppe-result.json')
    with open(dst_filename, 'w') as fd:
        json.dump(filtered_res,fd)
    print(filtered_res["PersonsWithoutRequiredEquipment"][0])
    assert filtered_res["Summary"]["SumPeopleWithoutRequiredEquipment"] == 4
    assert filtered_res["PersonsWithoutRequiredEquipment"][0]["MISSING_MASK"] == False
    assert filtered_res["PersonsWithoutRequiredEquipment"][0]["MISSING_HELMET"] == True
