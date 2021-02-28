import os
import json

from numpy.testing._private.utils import assert_

from main.graphql.mutation_preparer import prepare_mutation


def test_prepare_mutation():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/resp.json')
    with open(src_filename, 'r') as fd:
        msg = json.load(fd)
    camera_name = msg["cameraId"]
    ts = msg["ts"]

    face_res_filepath = os.path.join(src_dirname, '../data/face-res.json')
    with open(face_res_filepath, 'r') as fd:
        res = json.load(fd)

    
    mutation, variables = prepare_mutation(msg, [res])
    
    print(variables)
    assert variables["ts"] == 'das'
    assert variables["cameraId"] == camera_name
    assert variables["persons"][0]["faceId"] == res["FaceMatches"][0]["Face"]["FaceId"]
