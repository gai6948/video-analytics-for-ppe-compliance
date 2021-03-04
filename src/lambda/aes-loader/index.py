import base64

def handler(event, context):
    output = []
    # print(event)
    for record in event['Records']:
        data = base64.b64decode(record["kinesis"]["data"])
        print(data)
        newItem = data["dynamodb"]["NewImage"]
        
        # output_record = {
        #     'recordId': record['recordId'],
        #     'result': 'Ok',
        #     'data': str(record['data'])
        # }
        # output.append(output_record)
    # print('Successfully processed {} records.'.format(len(event['records'])))
    return {'records': output}
