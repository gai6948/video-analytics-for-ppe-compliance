import timeit
from typing import Tuple

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='face-detector', child=True)
tracer = Tracer(service='face-detector')

@tracer.capture_method(capture_response=False)
def prepare_mutation(message: dict, face_res: list, persons_detected: bool, detect_helmet: str) -> Tuple[dict, dict]:
    start_time = timeit.default_timer()

    mutation = """
        mutation NewAlarm(
            $cameraId: String!,
            $ts: String!,
            $persons: [PersonInput],
            $s3url: String,
            $status: String) {
                newAlarm(
                    cameraId: $cameraId,
                    ts: $ts,
                    persons: $persons,
                    s3url: $s3url,
                    status: $status
                ) {
                    persons {
                        faceId
                    }
                }
            }
    """

    cameraId = message["cameraId"]
    ts = message["ts"]
    persons = []
    person_count = 0

    if persons_detected:
        sts = "ACTIVE" 
        for detected_face in face_res:
            person = {
                "id": person_count,
                "boundingBox": {
                    "width": detected_face["SearchedFaceBoundingBox"]["Width"],
                    "height": detected_face["SearchedFaceBoundingBox"]["Height"],
                    "left": detected_face["SearchedFaceBoundingBox"]["Left"],
                    "top": detected_face["SearchedFaceBoundingBox"]["Top"],
                },
                "missingMask": message["ppeResult"]["personsWithoutRequiredEquipment"][person_count]["missingMask"],
                "faceId": detected_face["FaceMatches"][0]["Face"]["FaceId"]
            }
            if detect_helmet == 'true':
                person["missingHelmet"] = message["ppeResult"]["personsWithoutRequiredEquipment"][person_count]["missingHelmet"]
            persons.append(person)
            person_count += 1
    else:
        sts = "PENDING_REVIEW"

    variables = {
        "cameraId": cameraId,
        "ts": ts,
        "persons": persons,
        "s3url": message['s3url'],
        "status": sts
    }

    logger.info(
        f'Mutation preparation completed after: {timeit.default_timer() - start_time}')
    
    return mutation, variables
