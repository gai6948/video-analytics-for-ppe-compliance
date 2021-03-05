import logging
import base64
import os
# import datetime
import json
import boto3
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection, TransportError, AuthorizationException
from elasticsearch import helpers

logger = logging.getLogger('default')
host = os.environ["AES_HOST_URL"]
region = os.environ["AWS_REGION"]
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, 'es', session_token=credentials.token)

es = Elasticsearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)    

def handler(event, context):
    output = []
    actions = []
    # print(event)
    for record in event['Records']:
        data_byte_str = base64.b64decode(record["kinesis"]["data"])
        data_dict_str = data_byte_str.decode("utf-8")
        db_event = json.loads(data_dict_str)
        if db_event["eventName"] == "INSERT":
            newItem = db_event["dynamodb"]
            # print(newItem)
            timestamp = float(newItem["Keys"]["ts"]["S"])
            # event_time = datetime.datetime.utcfromtimestamp(timestamp).strftime("%Y/&")
            camera_id = newItem["Keys"]["cameraId"]["S"]
            ppe_result = newItem["NewImage"]["ppeResult"]["M"]
            # print(ppe_result)
            count_person_without_ppe = int(
                newItem["NewImage"]["ppeViolationCount"]["N"])
            ppl_count = int(newItem["NewImage"]["pplCount"]["N"])
            img_s3_url = newItem["NewImage"]["s3url"]["S"]
            persons = []
            if ppl_count >= 1:
                if ppl_count - count_person_without_ppe > 0:
                    for normal_ppl in ppe_result["personsWithRequiredEquipment"]["L"]:
                        append_person(persons, normal_ppl["M"])
                if count_person_without_ppe > 0:
                    for bad_ppl in ppe_result["personsWithoutRequiredEquipment"]["L"]:
                        append_person(persons, bad_ppl["M"])
            frame_document = {
                "camera_id": camera_id,
                "time": timestamp,
                "ppl_count": ppl_count,
                "violation_count": count_person_without_ppe,
                "persons": persons
            }
            print(frame_document)
            action = {
                "_index": "ppe_monitoring",
                "op_type": "index",
                "_source": frame_document
            }
            actions.append(action)
    try:
        aes_res = helpers.bulk(es, actions)
        print(aes_res)
    except AuthorizationException:
        print("Error loading data to AES: Unauthorized")
        # output_record = {
        #     'recordId': record['recordId'],
        #     'result': 'Ok',
        #     'data': str(record['data'])
        # }
        # output.append(output_record)
    # print('Successfully processed {} records.'.format(len(event['records'])))
    # return {'records': output}


def append_person(persons, ppl):
    missing_mask = ppl["missingMask"]["BOOL"]
    missing_Helmet = ppl["missingHelmet"]["BOOL"]
    ppl_id = int(ppl["id"]["N"])
    persons.append({
        "ppl_id": ppl_id,
        "missing_helmet": missing_Helmet,
        "missing_mask": missing_mask
    })
    return persons
