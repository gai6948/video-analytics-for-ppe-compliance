import os
import json

from main.graphql.mutation_executor import make_mutation

GRAPHQL_API_ENDPOINT = os.environ["GRAPHQL_API_ENDPOINT"]

def test_mutation_execution():

    # src_dirname = os.path.dirname(__file__)
    # src_filename = os.path.join(src_dirname, '../data/mutation-variables.json')
    # with open(src_filename, 'r') as fd:
    #     variables = json.load(fd)

    mutation = """
        mutation UpdateFrame(
            $cameraId: String!,
            $ts: String!,
            $persons: [PersonInput]) {
                updateFrame(
                    cameraId: $cameraId,
                    ts: $ts,
                    persons: $persons
                ) {
                    Persons {
                        faceId
                    }
                }
            }
    """

    variables = {
        'cameraId': 'test-laptop-01',
        'ts': '1611744890532',
        'persons': [
            {
                'id': 0, 
                'boundingBox': {
                    'width': 0.29546138644218445, 
                    'height': 0.43603354692459106,
                    'left': 0.43618500232696533,
                    'top': 0.16564273834228516
                },
                'missingMask': True,
                'missingHelmet': True,
                'faceId': '5fec5fae-9f92-401e-ac43-df1283ea5f12'
            }
        ]
    }

    res = make_mutation(mutation, variables, GRAPHQL_API_ENDPOINT)

    assert res is not None
