import boto3
import os
import json
from pprint import pprint


if __name__ == '__main__':
    results = []
    directory = os.fsencode('Camera Roll')
    imgs = os.listdir(directory)
    s3 = boto3.resource('s3')
    collection = 'rek-collection'
    bucket = s3.Bucket('rekog-bucket2')
    client = boto3.client('rekognition', 'us-east-2')
    i = 1
    for img in imgs:
        params = {
            'S3Object': {
                'Bucket': bucket.name,
                'Name': f'img{i}.jpg'
            }
            
        }
        

        results.append(client.index_faces(CollectionId=collection,Image=params, DetectionAttributes= [
                'DEFAULT'
        ], ExternalImageId = f'img{i}.jpg'))
        print(client.list_faces(CollectionId=collection))
        print(i)
        print('\n\n')
        i+=1
    print(results)
    print(client.list_faces(CollectionId=collection))
    