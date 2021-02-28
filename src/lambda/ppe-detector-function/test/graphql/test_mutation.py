import os
import json

from main.graphql.mutation import make_mutation

def test_mutation_execution():

    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/mutation-variables.json')
    with open(src_filename, 'r') as fd:
        variables = json.load(fd)

    mutation = """
        mutation InjestFrame(
            $cameraId: String!,
            $ts: String!,
            $s3url: String,
            $ppeResult: PPEResultInput
            $ppeViolationCount: Int
            $pplCount: Int) {
                injestFrame(
                    cameraId: $cameraId,
                    ts: $ts,
                    s3url: $s3url,
                    ppeResult: $ppeResult
                    ppeViolationCount: $ppeViolationCount
                    pplCount: $pplCount
                ) {
                    cameraId
                    ts
                    s3url
                }
            }
    """

    variables = {
        "cameraId": 'test-laptop-01',
        "s3url": 'prod-frameprocessorstack-framebucket6a445548-1o2vm6nfi5pyq/test-laptop-1-2021-01-08-08:27:53:985000.jpg',
        "ts": '1000000',
        "ppeResult": {
            "personsWithRequiredEquipment": {},
            "personsWithoutRequiredEquipment": {}
        },
        "ppeViolationCount": 0,
        "pplCount": 1
    }


    res = make_mutation(mutation, variables)

    assert res is not None
