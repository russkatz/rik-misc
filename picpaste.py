from flask import Flask, render_template, request
from flask_uploads import UploadSet, configure_uploads, IMAGES
from werkzeug.utils import secure_filename
import os
import random
import uuid

app = Flask(__name__)

photos = UploadSet('photos', IMAGES)

app.config['UPLOADED_PHOTOS_DEST'] = '/var/www/html/images/'
configure_uploads(app, photos)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST' and 'photo' in request.files:
        image = str(uuid.uuid4()) + ".jpg"
        filename = photos.save(request.files['photo'], "./", image)
        return " <HTML><BODY>url: http://sysop.estranger.net/images/%s <BR>delete: http://sysop.estranger.net:5000/delete/%s </BODY></HTML>" % (image,image)
    return render_template('upload.html')

@app.route('/delete/<string:image>/', methods=['GET'])
def delete(image):
   filename = '/var/www/html/images/' + image
   os.chmod(filename, 000)
   return "Deleted!"

if __name__ == '__main__':
    app.run(debug=True)
