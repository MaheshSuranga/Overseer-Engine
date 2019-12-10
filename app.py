from flask import Flask, render_template, request, Response, redirect, url_for, flash
from werkzeug import secure_filename
import os
import utils.videoSender as video_sender
import core.extract_embeddings as embeddings_extractor
import core.train_model as classfier
import core.recognize_video as recognizer
from flask_toastr import Toastr
import io
import pandas as pd
import threading

app = Flask(__name__)
toastr = Toastr(app)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

UPLOAD_FOLDER = 'dataset'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'} 

@app.route('/')
def index():
    return render_template('home.html')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload/',methods = ['GET','POST'])
def upload_file():
    if request.method =='POST':
        empName = request.form['name']
        fileList = request.files.getlist('file[]')

        vidFile = request.files['file']

        if fileList:
            saveLocation = os.path.sep.join([app.config['UPLOAD_FOLDER'],empName])
            if not (os.path.exists(saveLocation)):
                os.mkdir(saveLocation)
            for f in fileList:
                filename = secure_filename(f.filename.split('/')[1])
                f.save(os.path.join(saveLocation,filename))
            
        
        video_sender.send_train_video(empName, vidFile)
        flash(u'New employee was successfully registered!', 'success')
        return redirect(url_for('index'))
        # if 'file[]' not in request.files:
        #     flash('No file part')
        #     return "No file part"
        # file = request.files['file']
        # if file.filename == '':
        #     print("********")
        #     flash('No selected file')
        #     return "No file selected"
        # if file and allowed_file(file.filename):
        #     flash("file attached")
        #     filename = secure_filename(file.filename)
        #     file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #     return 'Home'
            # return redirect(url_for('uploaded_file',
            #                         filename=filename))
        # print(request.files.popitem)
        
        # return request

    return "render_template('file_upload.html')"
@app.route('/extraction/',methods = ['GET','POST'])
def extraction():
    if request.method == 'POST':
        confidence = request.form['range']
        num_of_embeddings = embeddings_extractor.extract_face_embeddings(confidence)
        flash(u'{} facial embeddings were extracted!'.format(num_of_embeddings), 'success')
        return render_template('home.html', number=str(num_of_embeddings))

@app.route('/train/',methods = ['GET','POST'])
def train():
    if request.method == 'POST':
        message = classfier.train_classifier()
        flash(u'The classifier was successfully trained!', 'success')
        return render_template('home.html', message=message)

@app.route('/surveillance/',methods = ['GET','POST'])
def surveillance():
    if request.method == 'POST':
        confidence = request.form['range1']
        vidFile = request.files['file1']
        filename = 'surveillance.mp4'
        vidFile.save(filename)

        vidFile.stream.seek(0)
        myfile = 'surveillance.mp4'
        # vidFile = vidFile.read()
        # vidFile = io.BytesIO(vidFile)
        # vidFile = vidFile.read()
        # vidFile = float(vidFile.read())
        # vidFile = int.from_bytes(vidFile, "little")

        # recognizer.recognize(confidence, myfile)

        t1 = threading.Thread(target=recognizer.recognize, args=(confidence, myfile))
        t2 = threading.Thread(target=video_sender.send_surveillance_video, args=[myfile])
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()  
        return render_template('video.html')

@app.route("/video_feed")
def video_feed():
	# return the response generated along with the specific media
	# type (mime type)
	return Response(recognizer.generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

if __name__ == '__main__':
    app.run(debug=True, threaded=True)