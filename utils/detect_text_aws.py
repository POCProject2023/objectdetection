import pandas as pd
import boto3
from botocore.exceptions import ClientError

credential = pd.read_csv("asif_accessKeys.csv")
access_key_id = credential['Access key ID'][0]
secret_access_key = credential['Secret access key'][0]

client = boto3.client('rekognition', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key,region_name='us-east-1')


def get_text(img):
    try:
        filename = img
        img = 'static/uploads/' + filename

        with open(img, 'rb') as source_image:
            source_bytes = source_image.read()

        response = client.detect_labels(
            Image={
                'Bytes': source_bytes
            })

        detected_objects = []

        for label in response['Labels']:
            detected_objects.append({
                'Name': label['Name'],
                'Confidence': label['Confidence']
            })

        statement = "success"
        return detected_objects, filename, statement

    except Exception as e:
        print("Error:", e)
        statement = "Something went wrong: " + str(e)
        return None, None, statement




