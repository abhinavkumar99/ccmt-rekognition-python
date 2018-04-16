import boto3

s3 = boto3.resource('s3')
client = boto3.client('rekognition')
sclient = boto3.client('s3')
bucket = s3.Bucket('rekog-bucket2')
collection = 'x'
imgs = sclient.list_objects(Bucket='rekog-bucket2')

with open('inv.csv', 'r') as inv:
    for line in inv:
        key = line.split(',')[1]
        if not any(d['Key'] == key for d in imgs['Contents']):
            client.index_faces(
                CollectionId=collection,
                Image = {
                    'S3Object': {
                        'Bucket': bucket.name,
                        'Name': key[:-4],
                    }
                },
                ExternalImageId=key,
                DetectionAttributes = [
                    'DEFAULT'
                ]
            )
            print('indexed: ' + str(key))

