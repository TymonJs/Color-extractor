from flask import Flask, flash, render_template, redirect, url_for,request
from flask_bootstrap import Bootstrap
from forms import ColorForm
from os import environ, mkdir,listdir,remove
from werkzeug.utils import secure_filename
from random import randint
from PIL import Image
from numpy import array, uint8
from time import perf_counter

PIXEL_DISTANCE = 25
COLOR_DISTANCE = 100
BW_DISTANCE = 50

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

def get_pixels(path:str,amount=10,frame = 0):
    img = Image.open(path)
    if path.endswith(".gif"):
        img.seek(frame)
    index = 1
    dict = {}
    for row in array(img):
        for value in row:
            if index % PIXEL_DISTANCE == 0:

                if type(value) == uint8:
                    value = (value,value,value)
               
                else:
                    value = tuple(value.tolist()[:3])

                if value not in dict:
                        if index !=1:
                            if clr_distance(value,(0,0,0)) < BW_DISTANCE or clr_distance(value,(255,255,255)) < BW_DISTANCE:
                                continue
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
    else:
        for file in listdir(app.config['UPLOAD_FOLDER']):
            remove(app.config["UPLOAD_FOLDER"]+file)

    form = ColorForm()
    if request.method == 'POST':

        file = request.files['color']

        if file.filename == '':
            flash("File hasn't been selected")
            return redirect(url_for('home'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            path = app.config['UPLOAD_FOLDER'] + filename

            file.save(path)
            
            hexs = get_pixels(path)
            
            return render_template('index.html', form=form, path=path,clrs=hexs)
            
        else:
            flash("File not allowed")
            return redirect(url_for('home'))
    return render_template('index.html',form=form)

if __name__ == "__main__":
    app.run(debug=False)

# jeżeli gif to spytaj którą klatke wybrać (default zero)
# Jeżeli poptrzedni pixel jest bardzo podobny do obecnego to nie sprawdzaj go (continue) 