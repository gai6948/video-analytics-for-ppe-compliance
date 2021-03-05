import timeit

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


logger = Logger(service='ppe-detector', child=True)
tracer = Tracer(service='ppe-detector')


@tracer.capture_method(capture_response=False)
def filter_result(ppe_res: dict, min_confidence: int, detect_helmet: str) -> dict:
    """
    Handle the response from PPE detection and filter out person not wearing mask and helmet
    Combining results of "PersonsIndeterminate" and "PersonsWithoutRequiredEquipment" by context
    """

    start_time = timeit.default_timer()
    # List of Id of people violating PPE guidelines
    incompliant_list = ppe_res["Summary"]["PersonsWithoutRequiredEquipment"]
    incompliant_list += ppe_res["Summary"]["PersonsIndeterminate"]
    ppl_without_equipment = []  # List of people violating PPE guidelines
    ppl_without_equipment_idx = 0
    ppl_with_equipment = []
    resp = {}

    if len(incompliant_list) >= 1:
        persons = ppe_res["Persons"]
        for person in persons:
            if person["Id"] in incompliant_list:
                ppl_without_equipment.append(person)
                face_checked = False
                head_checked = False
                for bp in person["BodyParts"]:
                    if bp["Name"] == "FACE":
                        if not bp["EquipmentDetections"] or bp["EquipmentDetections"][0]["Confidence"] <= min_confidence:
                            ppl_without_equipment[ppl_without_equipment_idx]["MISSING_MASK"] = True
                        else:
                            ppl_without_equipment[ppl_without_equipment_idx]["MISSING_MASK"] = False
                        face_checked = True
                    if detect_helmet == "true":
                        if bp["Name"] == "HEAD":
                            if not bp["EquipmentDetections"] or bp["EquipmentDetections"][0]["Confidence"] <= min_confidence:
                                ppl_without_equipment[ppl_without_equipment_idx]["MISSING_HELMET"] = True
                            else:
                                ppl_without_equipment[ppl_without_equipment_idx]["MISSING_HELMET"] = False
                            head_checked = True
                if face_checked == False:
                    ppl_without_equipment[ppl_without_equipment_idx]["MISSING_MASK"] = True
                if detect_helmet == "true":
                    if head_checked == False:
                        ppl_without_equipment[ppl_without_equipment_idx]["MISSING_HELMET"] = True
                ppl_without_equipment_idx += 1
            else:
                ppl_with_equipment.append(person)

    resp["PersonsWithoutRequiredEquipment"] = ppl_without_equipment
    resp["PersonsWithRequiredEquipment"] = ppl_with_equipment
    resp["Summary"] = {}
    resp["Summary"]["SumPeopleWithRequiredEquipment"] = len(
        ppe_res["Persons"]) - len(incompliant_list)
    resp["Summary"]["SumPeopleWithoutRequiredEquipment"] = len(
        incompliant_list)

    logger.info(
        f'{len(incompliant_list)} people detected without protective equipment')
    logger.info(
        f'Filtering result completed after: {timeit.default_timer() - start_time}')

    return resp
