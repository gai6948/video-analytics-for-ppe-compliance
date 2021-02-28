import os
import json
from main.ppedetection.notifier import notify_alarm


topic_arn = os.environ["SNS_TOPIC_ARN"]
def test_notify_alarm():
    src_dirname = os.path.dirname(__file__)
    src_filename = os.path.join(src_dirname, '../data/ppe-result.json')
    with open(src_filename, 'r') as fd:
        ppe_res = json.load(fd)
    status = notify_alarm(topic_arn, ppe_res)
    assert status == True
