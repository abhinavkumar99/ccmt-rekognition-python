import boto3
from PIL import Image
import os
import io
import base64
import json

from chalice import Chalice, Response, Rate
app = Chalice(app_name='helloworld')
s3 = boto3.resource('s3')
collection = 'rek-collection'
bucket = s3.Bucket('rekog-bucket2')
client = boto3.client('rekognition', 'us-east-2')
sclient = boto3.client('s3')
data = client.list_faces(CollectionId='rek-collection')
imgs = sclient.list_objects(Bucket='rekog-bucket2')
def propagate_person_id(faces, faceId):
    
    for matchingId in faces[faceId]['FaceMatches']:
        mid = faces[faceId]['FaceMatches'][matchingId]
        if'PersonId' not in faces[mid]:
            numberMatchingLoops = 0

            for matchingId2 in faces[mid]['FaceMatches']:
                mid2 = faces[mid]['FaceMatches'][matchingId2]

                if faceId not in faces[mid2]['FaceMatches']:
                    numberMatchingLoops += 1
            if numberMatchingLoops >= 2:
                personId = faces[faceId]['PersonId']
                faces[mid]['PersonId'] = personId
                faces = propagate_person_id(faces,mid)
    return faces

ret = {}
faces = {}
@app.schedule(Rate(1, unit=Rate.DAYS))
def handler(event):
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


    global ret
    global faces
    ret = {}
    faces = {}
    #Currently groups all images. Add thing to group based only on input image
    for face in data['Faces']:
        
        key = face['FaceId']

        ids = face['ExternalImageId']
        box = face['BoundingBox']
        faces[key] = {
            'ExternalImageId': ids,
            'BoundingBox': box 
        }
        queueData = client.search_faces(CollectionId = 'rek-collection', FaceId=key, MaxFaces=4096, FaceMatchThreshold=75)
        matches = {}
        for i in range(len(queueData['FaceMatches'])):
            matches[i] = queueData['FaceMatches'][i]['Face']['FaceId']
        faces[key]['FaceMatches'] = matches


    personId = 0
    for faceId in faces:
        if 'PersonId' not in faces[faceId]:
            personId = personId + 1
            faces[faceId]['PersonId'] = personId
            faces = propagate_person_id(faces, faceId)

    for faceId in faces:
        bb = faces[faceId]['BoundingBox']
        personId = faces[faceId]['PersonId']
        print("Downloading..." + faces[faceId]['ExternalImageId'])

        obj = sclient.get_object(
            Bucket = 'rekog-bucket2',
            Key=faces[faceId]['ExternalImageId']
        )
        img = Image.open(io.BytesIO(obj['Body'].read()))
        width, height=img.size
        b = []
        b.append(width)
        b.append(height)
        bbwidth = bb['Width']
        bbheight = bb['Height']
        bbx = bb['Left']
        bby = bb['Top']
        width = b[0]*bbwidth
        height = b[1]*bbheight
        x = b[0]*bbx
        y = b[1]*bby
        img = img.crop((x, y, width + x, height + y))
        
        buffered = io.BytesIO()

        img.save(buffered, format='PNG')
        if personId not in ret:
            ret[personId] = []
        ret[personId].append(base64.b64encode(buffered.getvalue()).decode('utf-8'))



@app.route('/')
def index():
    return ret

@app.route('/faces',methods = ['POST'], content_types = ['application/octet-stream'])
def search():

    return client.search_faces_by_image(CollectionId=collection, Image={'Bytes': app.current_request.raw_body})['FaceMatches']
