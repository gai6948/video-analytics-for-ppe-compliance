import base64

def handler(event, context):
    output = []
    for record in event['records']:
        data = base64.b64decode(record["data"])
        print(data)     
        # output_record = {
        #     'recordId': record['recordId'],
        #     'result': 'Ok',
        #     'data': str(record['data'])
        # }
        # output.append(output_record)
    # print('Successfully processed {} records.'.format(len(event['records'])))
    return {'records': output}
