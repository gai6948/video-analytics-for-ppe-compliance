import os
import json

from main.graphql.mutation_preparer import prepare_mutation


def test_prepare_mutation():
    camera_name = 'test-laptop-1'
    filename = 'test-laptop-1-2021-01-08-08:27:53:985000.jpg'
    timestamp = '1610094473985'

    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/filtered-ppe-result.json')
    with open(src_filename, 'r') as fd:
        filtered_res = json.load(fd)

    test_filename = os.path.join(src_dirname, '../data/mutation-variables.json')
    with open(test_filename, 'r') as fd:
        expected_res = json.load(fd)

    mutation, variable = prepare_mutation(camera_name, filename, timestamp, filtered_res)
    print(variable)

    dst_dirname = os.path.dirname(__file__)
    dst_filename = os.path.join(dst_dirname, '../output/graphql-mutation.json')
    with open(dst_filename, 'w') as fd:
        json.dump(variable, fd)

    assert variable["ts"] == '1610094473985'
    assert variable["ppeResult"]["summary"]["sumPeopleWithoutRequiredEquipment"] == 4
    assert variable["ppeResult"]["personsWithoutRequiredEquipment"][0]["missingMask"] == False
    assert variable["ppeResult"]["personsWithoutRequiredEquipment"][0]["missingHelmet"] == True
    
    assert variable["ppeResult"]["personsWithoutRequiredEquipment"][0]["boundingBox"]["width"] == 0.432467520236969
    assert variable["ppeResult"]["personsWithoutRequiredEquipment"][1]["boundingBox"]["height"] == 0.9838337302207947
    assert variable["ppeResult"]["personsWithoutRequiredEquipment"][2]["boundingBox"]["left"] == 0.50649350881576542
