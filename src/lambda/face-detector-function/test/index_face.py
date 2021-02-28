import boto3
import os

client = boto3.client('rekognition')

dirname = os.path.dirname(__file__)
filename = os.path.join(dirname, 'data/raw-java-frame.png')
fp = open(filename, 'rb')
blob_bytes = fp.read()

response = client.index_faces(
    CollectionId='test-collection-01',
    Image={
        'Bytes': blob_bytes,
    },
    MaxFaces=123,
    QualityFilter='AUTO'
)

print(response)
