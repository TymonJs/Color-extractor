from collections import Counter
from sys import maxsize
from threading import Thread
from cv2 import VideoCapture
from flask import Flask, flash, render_template, redirect, url_for,request,abort,after_this_request,jsonify
from flask_bootstrap import Bootstrap
from forms import ColorForm, GifForm
from os import environ, mkdir,listdir,remove
from werkzeug.utils import secure_filename
from PIL import Image
from numpy import array, uint8
from time import sleep
from random import randint
import cv2

PIXEL_DISTANCE = 25
COLOR_DISTANCE = 100
BW_DISTANCE = 60

MAX_FILE_SIZE = 50 #MB

VIDEO_EXTENSIONS = {'mp4'}
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png','gif'} | VIDEO_EXTENSIONS

UPLOAD_FOLDER = './static/uploads/'

app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('secret_key')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = maxsize * 1024 * 1024

Bootstrap(app)
static = listdir("./static/")
if "uploads" not in static:
    mkdir("./static/uploads")

def clr_distance(clr1,clr2):
    delta_r = clr1[0] - clr2[0]
    delta_g = clr1[1] - clr2[1]
    delta_b = clr1[2] - clr2[2]
    red_mean = 1/2*(clr1[0] + clr2[0])
    distance = ((2+red_mean/256)*(delta_r**2) + 4*(delta_g**2) + (2 + (255-red_mean)/256)* (delta_b**2) )**(1/2)
    return distance

def get_pixels(path:str,amount=10):
    try:
        img = Image.open(path)
    except FileNotFoundError:
        return redirect(url_for('home'))
    index = 1
    dict = {}
    for row in array(img):
        for value in row:
            if index % PIXEL_DISTANCE == 0:

                if type(value) == uint8:
                    value = int(value)
                    value = (value,value,value)
               
                else:
                    value = tuple(value.tolist()[:3])

                if value not in dict:
                        if index !=1:
                            # if clr_distance(value,(0,0,0)) < BW_DISTANCE or clr_distance(value,(255,255,255)) < BW_DISTANCE:
                            #     continue
                            for element in dict:
                                if clr_distance(value,element) < COLOR_DISTANCE:
                                    break
                            else:
                                dict[value] = 1
                        else:       
                            dict[value] = 1
                else:
                    dict[value]+=1

            index+=1

    dict = sorted(dict.items(), key=lambda x: x[1], reverse=True)[:amount]
    hexs = []
    for value in dict:
        hexs.append(rgb_to_hex(value[0]))
    return hexs


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def rgb_to_hex(clrs):
    hexCode = "#"
    for val in clrs:
        val = hex(val)
        if len(val) != 4:
            hexCode+="0"
        hexCode+= (str(val).replace("0x","").upper())
    return hexCode

@app.errorhandler(413)
def largefile_error(e):
    flash(F'File too large. Max file size is {MAX_FILE_SIZE}MB')
    return redirect(url_for('home'))
    # return jsonify(
    # {
    #     "Error":str(e),
    #     "Click to redirect":url_for('home')
    # }
    # ),413

@app.errorhandler(403)
def user_not_allowed(e):
    return jsonify(
        {
            "Error":str(e),
            "Click to redirect":url_for('home')
        }
    ),403

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify(
        {
            "Error":str(e),
            "Click to redirect":url_for('home')
        }
    ),405

@app.route("/",methods=['GET','POST'])
def home():
    
    form = ColorForm()
    if request.method == 'POST':

        file = request.files['color']

        if file.filename == '':
            flash("File hasn't been selected")
            return redirect(url_for('home'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            extension = filename.split(".")[-1]
            while filename in listdir(app.config["UPLOAD_FOLDER"]):
                filename=filename.rsplit('.',1)[0] +"_"+str(randint(1,1000000))+"."+extension
            path = UPLOAD_FOLDER + filename

            if extension not in VIDEO_EXTENSIONS:
                file.save(path)
                if filename.endswith(".gif") and Image.open(file).n_frames > 1:
                    return redirect(url_for('gif',filename=filename))
            else:
                with open(app.config["UPLOAD_FOLDER"] + filename,'wb') as f:
                    f.write(file.stream.read())

                return redirect(url_for('video',filename=filename))

            hexs = get_pixels(path)

            afterReturnRemove(path)

            return render_template('index.html', path=path,clrs=hexs)
            
        else:
            flash("File not allowed")
            return redirect(url_for('home'))
    return render_template('index.html',form=form)

@app.route('/video',methods=['GET','POST'])
def video():

    filename = request.args.get("filename")
    form = GifForm()

    if not filename:
        abort(403)
    path = UPLOAD_FOLDER + filename

    vid = cv2.VideoCapture(path)
    fps = vid.get(cv2.CAP_PROP_FPS) 
    frame_count = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

    try:
        seconds_total = frame_count//fps
        minutes = int(seconds_total/60)
        seconds = str(int(seconds_total-minutes*60))
    except:
        try:
            remove(path)
        except FileNotFoundError:
            pass
        finally:
            flash("Session expired")
            return redirect(url_for('home'))
    
    if len(seconds) == 1:
        seconds = "0"+seconds

    duration_str = f"{minutes}:{seconds}"

    shape = {
        "width":vid.get(cv2.CAP_PROP_FRAME_WIDTH),
        "height":vid.get(cv2.CAP_PROP_FRAME_HEIGHT),
        'max-w':800,
        'max-h':600
    }

    Thread(target=afterReturnRemove(path,60)).start()
    return render_template('frame-select.html',form=form,dur=duration_str,path=path,shape=shape)

@app.route('/video-validate',methods=['POST'])
def videoValidate():
    form = GifForm()
    path = request.args.get("path")
    filename = path.replace(UPLOAD_FOLDER,'')
    frame:str = form.frame.data

    vid = cv2.VideoCapture(path)
    fps = vid.get(cv2.CAP_PROP_FPS) 
    frame_count = int(vid.get(cv2.CAP_PROP_FRAME_COUNT))

    if not frame:
        frame = 0

    else:
        for _ in range(1):
            if ":" in frame:
                minute,second = frame.split(":")
                

            elif ":" not in frame:
                frame = frame.strip(" ")
                spaces = Counter(frame)[" "]
                if spaces == 1:
                    minute,second = frame.split(" ")
                elif spaces == 0:
                    frame = int(frame)
                    if frame>=0:
                        frame = frame * fps
                        continue
                    else:
                        flash("Frame doesn't exist")
                        return redirect(url_for('video',filename=filename))

                else:
                    flash("Frame doesn't exist")
                    return redirect(url_for('video',filename=filename))

            frame = int((int(minute)*60+int(second))*fps)

    if frame>frame_count:
        flash("Frame doesn't exist")
        return redirect(url_for('video',filename=path.replace(UPLOAD_FOLDER,'')))

    vid.set(cv2.CAP_PROP_POS_FRAMES, frame)
    success,frame = vid.read()
    if not success:
        flash("Session expired")
        return redirect(url_for('home'))

    name = path.rsplit('.',1)[0] + '.png'
    cv2.imwrite(name, frame)

    vid.release()
    cv2.destroyAllWindows()


    # if filename in listdir(UPLOAD_FOLDER):
    #     remove(path)

    hexs = get_pixels(name)

    afterReturnRemove(name)
    afterReturnRemove(path)
    return render_template('index.html',path=name,clrs=hexs)


def afterReturnRemove(path,time=10):
    @after_this_request
    def wrapper(response):
        @response.call_on_close
        def afterwork():
            try:
                removeUpload(path,time)
            except:
                pass
        return response

@app.route("/gif",methods=["GET",'POST'])
def gif():
    filename = request.args.get("filename")
    form = GifForm()

    if not filename:
        abort(403)

    path = UPLOAD_FOLDER+filename
    file = Image.open(path)


    Thread(target=afterReturnRemove(path,60)).start()
    return render_template('frame-select.html',form=form,file=file,path=path)

@app.route('/gif-validate',methods=["POST"])
def gifValidate():
    form = GifForm()
    path = request.args.get("path")
    file = Image.open(path)

    frame = form.frame.data
    if frame or frame == 0:
        frame=int(frame)-1  

    if (not frame or frame < 1) and file.n_frames>1:
        frame = 1
    
    if frame not in range(0,file.n_frames-1):
        flash("Frame doesn't exist")
        return redirect(url_for('gif',filename=path.replace(UPLOAD_FOLDER,'')))
    file.seek(frame)
    pathPng = path.rstrip("gif") + 'png'
    file.save(pathPng)
    file.close()
    remove(path)
    
    return redirect(url_for('gifColors',path=pathPng))



# @app.context_processor
# def utility_processor():
#     def removeUpload(path):
#         sleep(5)
#         remove(path)
#     return dict(removeUpload=removeUpload)

def removeUpload(path,time=5):
    sleep(time)
    remove(path)

@app.route('/gif-colors',methods=["GET"])
def gifColors():
    path = request.args.get("path")
    if path:
        hexs = get_pixels(path)
        
        afterReturnRemove(path)
        try:
            return render_template('index.html',path=path,clrs=hexs)
        except TypeError:
            abort(403)
            
    else:
        abort(403)

if __name__ == "__main__":
    app.run(debug=True)

# Jeżeli poptrzedni pixel jest bardzo podobny do obecnego to nie sprawdzaj go (continue) 
# form range 


### W przyszłości z js - gdy wybierasz klatke do gifa przesuwaj suwakiem żeby wybrać klatkę (gif się synchronicznie zmienia)