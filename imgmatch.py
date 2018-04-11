import boto3
import os
from PIL import Image
import io

s3 = boto3.resource('s3')
collection = 'rek-collection'
bucket = s3.Bucket('rekog-bucket2')
client = boto3.client('rekognition', 'us-east-2')
sclient = boto3.client('s3')
data = client.list_faces(CollectionId='rek-collection')
queue = []
faces = {}
def crop(faceId, imgId, bb, personId):
    print("Downloading..." + faceId)
    obj = sclient.get_object(
        Bucket = 'rekog-bucket2',
        Key=imgId
    )
    img = Image.open(io.BytesIO(obj['Body'].read()))
    width, height = img.size
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
    img = img.crop((x,y,width+x, height+y))
    try:
        os.makedirs(f'faces\\{str(personId)}')
        img.save(f'faces\\{str(personId)}\\{str(faceId)}.jpg')
    except:
        img.save(f'faces\\{str(personId)}\\{str(faceId)}.jpg')





def group_images(key, id, box):
    global faces
    global queue
    queueData = client.search_faces(CollectionId = 'rek-collection', FaceId=key, MaxFaces=4096, FaceMatchThreshold=75)
    matches = {}
    for i in range(len(queueData['FaceMatches'])):
        matches[i] = queueData['FaceMatches'][i]['Face']['FaceId']
    faces[key]['FaceMatches'] = matches

def propagate_person_id(faceId):
    global faces
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
                propagate_person_id(mid)            



for face in data["Faces"]:
   key = face['FaceId']

   ids = face['ExternalImageId']
   box = face['BoundingBox']
   faces[key] = {
       'ExternalImageId': ids,
       'BoundingBox': box 
   }
   group_images(key, ids, box)
personId = 0
for faceId in faces:
    if 'PersonId' not in faces[faceId]:
        personId = personId + 1
        faces[faceId]['PersonId'] = personId
        propagate_person_id(faceId)
for faceId in faces:
    print("face Id "+faceId +" Person Id "+ str(faces[faceId]['PersonId']) )
    crop(faceId, faces[faceId]['ExternalImageId'], faces[faceId]['BoundingBox'], faces[faceId]['PersonId'])