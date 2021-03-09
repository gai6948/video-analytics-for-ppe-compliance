import os
import timeit
from typing import Tuple

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')


@tracer.capture_method(capture_response=False)
def prepare_mutation(camera_name: str, filename: str, timestamp: str, filtered_response: dict, detect_helmet: bool) -> Tuple[dict, dict]:
    """
    Transform data into GraphQL Schema compliant format

    @param `filtered_response` dict returned from `filter_result` function
    """

    start_time = timeit.default_timer()

    pplWithEquipment = []
    for person in filtered_response["PersonsWithRequiredEquipment"]:
        ppl_with_equipment = {
            "id": person["Id"],
            "missingMask": False,
            "missingHelmet": False,
            "boundingBox": {
                "width": person["BoundingBox"]["Width"],
                "height": person["BoundingBox"]["Height"],
                "left": person["BoundingBox"]["Left"],
                "top": person["BoundingBox"]["Top"]
            }
        }
        if detect_helmet == True:
            ppl_with_equipment["missingHelmet"] == False
        pplWithEquipment.append(ppl_with_equipment)

    pplWithoutEquipment = []
    for person in filtered_response["PersonsWithoutRequiredEquipment"]:
        ppl_without_equipment = {
            "id": person["Id"],
            "missingMask": True if person["MISSING_MASK"] == True else False,
            "boundingBox": {
                "width": person["BoundingBox"]["Width"],
                "height": person["BoundingBox"]["Height"],
                "left": person["BoundingBox"]["Left"],
                "top": person["BoundingBox"]["Top"]
            }
        }
        if detect_helmet == True:
            ppl_without_equipment["missingHelmet"] == True if person["MISSING_HELMET"] == True else False
        pplWithoutEquipment.append(ppl_without_equipment)

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
        "cameraId": camera_name,
        "s3url": os.environ["PROCESSED_S3_BUCKET"] + "/" + filename,
        "ts": timestamp,
        "ppeResult": {
            "personsWithRequiredEquipment": pplWithEquipment,
            "personsWithoutRequiredEquipment": pplWithoutEquipment
        },
        "ppeViolationCount": filtered_response["Summary"]["SumPeopleWithoutRequiredEquipment"],
        "pplCount": filtered_response["Summary"]["SumPeopleWithoutRequiredEquipment"] + filtered_response["Summary"]["SumPeopleWithRequiredEquipment"]
    }

    logger.info(
        f'Mutation preparation completed after: {timeit.default_timer() - start_time}')

    return mutation, variables
