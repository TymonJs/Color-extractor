from threading import Thread
from flask import Flask, flash, render_template, redirect, url_for,request,abort,after_this_request
from flask_bootstrap import Bootstrap
from forms import ColorForm, GifForm
from os import environ, mkdir,listdir,remove
from werkzeug.utils import secure_filename
from PIL import Image
from numpy import array, uint8
from time import sleep
from random import randint
PIXEL_DISTANCE = 25
COLOR_DISTANCE = 100
BW_DISTANCE = 60

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png','gif',"svg"}

app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('secret_key')
app.config['UPLOAD_FOLDER'] = './static/uploads/'

Bootstrap(app)

def clr_distance(clr1,clr2):
    delta_r = clr1[0] - clr2[0]
    delta_g = clr1[1] - clr2[1]
    delta_b = clr1[2] - clr2[2]
    red_mean = 1/2*(clr1[0] + clr2[0])
    distance = ((2+red_mean/256)*(delta_r**2) + 4*(delta_g**2) + (2 + (255-red_mean)/256)* (delta_b**2) )**(1/2)
    return distance

def get_pixels(path:str,amount=10):
    img = Image.open(path)
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

@app.route("/",methods=['GET','POST'])
def home():

    static = listdir("./static/")
    if "uploads" not in static:
        mkdir("./static/uploads")
    
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
                filename+="_"+randint(1,1000000)
            path = app.config['UPLOAD_FOLDER'] + filename
            file.save(path)

            if filename.endswith(".gif") and Image.open(file).n_frames > 1:
                return redirect(url_for('gif',filename=filename))  

            hexs = get_pixels(path)

            @after_this_request
            def wrapper(response):

                @response.call_on_close
                def afterwork():

                    removeUpload(path)
                return response

            return render_template('index.html', path=path,clrs=hexs)
            
        else:
            flash("File not allowed")
            return redirect(url_for('home'))
    return render_template('index.html',form=form)

@app.route("/gif",methods=["GET",'POST'])
def gif():
    filename = request.args.get("filename")
    form = GifForm()

    if not filename:
        abort(403)

    path = app.config['UPLOAD_FOLDER']+filename
    file = Image.open(path)

    def task(time):
        @after_this_request
        def wrapper(response):
            @response.call_on_close
            def afterwork():
                try:
                    removeUpload(path,time)
                except:
                    pass
            return response

    Thread(target=task(30)).start()
    return render_template('frame-select.html',form=form,file=file,path=path)

@app.route('/gif-validate',methods=["POST"])
def gifValidate():
    form = GifForm()
    path = request.args.get("path")
    file = Image.open(path)

    frame = form.frame.data
    if frame:
        frame=int(frame)-1
    else:
        frame = 0
    
    if frame not in range(0,file.n_frames-1):
        flash("Frame doesn't exist")
        return redirect(url_for('gif',filename=path.replace(app.config['UPLOAD_FOLDER'],'')))
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
        
        @after_this_request
        def wrapper(response):

            @response.call_on_close
            def afterwork():
                removeUpload(path)
            return response

        return render_template('index.html',path=path,clrs=hexs)
            
    else:
        abort(403)

if __name__ == "__main__":
    app.run()

#unique files with ids 
# Jeżeli poptrzedni pixel jest bardzo podobny do obecnego to nie sprawdzaj go (continue) 

### W przyszłości z js - gdy wybierasz klatke do gifa przesuwaj suwakiem żeby wybrać klatkę (gif się synchronicznie zmienia)