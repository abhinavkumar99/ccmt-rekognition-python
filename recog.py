import boto3
import os

s3 = boto3.resource('s3')

bucket = s3.Bucket('rekog-bucket2')
i = 1
directory = os.fsencode('Camera Roll')
imgs = os.listdir(directory)


for img in imgs:
   bucket.upload_file(f'Camera Roll/{img.decode("ascii")}', f'img{i}.jpg')
   print(f'img{i}.jpg')
   i += 1
   
    

"""client = boto3.client('rekognition', 'us-east-2')
client.create_collection(
    CollectionId='rek-collection'
)

s3.index_faces()"""