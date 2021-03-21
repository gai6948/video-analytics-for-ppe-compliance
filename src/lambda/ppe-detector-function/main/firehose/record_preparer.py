import os
import timeit

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')


@tracer.capture_method(capture_response=False)
def prepare_record(camera_name: str, filename: str, timestamp: str, filtered_response: dict, detect_helmet: str) -> dict:
    """
    Transform data into JSON format for Firehose input

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
        if detect_helmet == "true":
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
        if detect_helmet == "true":
            ppl_without_equipment["missingHelmet"] == True if person["MISSING_HELMET"] == True else False
        pplWithoutEquipment.append(ppl_without_equipment)

    record = {
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
        f'Record preparation completed after: {timeit.default_timer() - start_time}')

    return record
