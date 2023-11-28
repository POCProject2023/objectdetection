import os
import io
import urllib.request
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from flask import Flask, flash, request, redirect, url_for, render_template,jsonify,json
from werkzeug.utils import secure_filename
from utils.detect_text_aws import  get_text
from botocore.exceptions import NoCredentialsError


UPLOAD_FOLDER = 'static/uploads/'

app = Flask(__name__)
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

credential = pd.read_csv("asif_accessKeys.csv")
AWS_ACCESS_KEY = credential['Access key ID'][0]
AWS_SECRET_KEY = credential['Secret access key'][0]
AWS_BUCKET_NAME = "object-training-bucket"
AWS_BUCKET_NAME2 = "object-rekognition-storage"

s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)


@app.route('/')
def start_page():
    return render_template('index.html')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



def generate_presigned_url(filename):
    key = "annonated_"+filename
    url = s3.generate_presigned_url(
        'get_object',
        Params={'Bucket': AWS_BUCKET_NAME2, 'Key': key},
        ExpiresIn=3600  # URL will expire in 1 hour
    )
    return url




@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        statement = 'No file part'
        return render_template('index.html', statement=statement)
    file = request.files['file']
    if file.filename == '':
        statement = 'No image selected for uploading'
        return render_template('index.html', statement=statement)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(file_path, 'wb') as f:
            file.save(f)

         # Upload the file to AWS S3
        
        # try:
        s3.upload_file(file_path, AWS_BUCKET_NAME, filename)
        # except NoCredentialsError:
        # return render_template('index.html', statement='AWS credentials not available. File not uploaded.')

        # Delete the local file after uploading to S3
        # os.remove(file_path)




        detected_objects, res_img, statement = get_text(filename)
        if statement == "success":
            return render_template('index.html', detected_objects=detected_objects, filename=res_img, statement=statement)
        else:
            return render_template('index.html', statement=statement)
    else:
        statement = 'Allowed image types are -> png, jpg, jpeg'
        return render_template('index.html', statement=statement)


@app.route('/display/<filename>')
def display_image(filename):
    #print('display_image filename: ' + filename)
    return redirect(url_for('static', filename='uploads/' + filename), code=301)


@app.route('/display_result_image/<filename>')
def display_result_image(filename):
    # Generate a pre-signed URL for the specific S3 object
    s3_url = generate_presigned_url(filename)
    return render_template('index.html', s3_url=s3_url)

# @app.route('/display_result_image/<filename>')
# def display_result_image(filename):
#     #print('display_image filename: ' + filename)
#     return redirect(url_for('static', filename='result/' + filename), code=301)

@app.after_request
def add_header(response):
    response.headers['Pragma'] = 'no-cache'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = '0'
    return response


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
