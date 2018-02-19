from flask import Flask, render_template, request
from flask_uploads import UploadSet, configure_uploads, IMAGES
from werkzeug.utils import secure_filename
import os
import random
import uuid
import boto3

app = Flask(__name__)
bucket = 'images.estranger.net'
s3 = boto3.resource('s3')

app.config['UPLOADED_PHOTOS_DEST'] = '/var/www/html/images/'

photos = UploadSet('photos', IMAGES)

configure_uploads(app, photos)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        image = str(uuid.uuid4()) + ".jpg"
        filename = photos.save(request.files['photo'], "./", image)
        uploadFile = str(app.config['UPLOADED_PHOTOS_DEST']) + filename
        data = open(uploadFile, 'rb')
        s3.Bucket(bucket).put_object(Key=image, Body=data, ACL='public-read', ContentType='image/jpeg')
        os.remove(uploadFile)
        return render_template('uploaded.html', image=image, bucket=bucket)
    return "NO!"

@app.route('/delete/<string:image>/', methods=['GET'])
def delete(image):
   object = s3.Bucket(bucket).Object(image)
   object.Acl().put(ACL='private')
   return render_template('deleted.html')

if __name__ == '__main__':
    app.run(debug=True)
