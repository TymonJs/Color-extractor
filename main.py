from flask import Flask, flash, render_template, redirect, url_for,request
from flask_bootstrap import Bootstrap
from forms import ColorForm
from os import environ, mkdir,listdir,remove
from werkzeug.utils import secure_filename
import colorgram

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png','gif',"svg"}
app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('secret_key')
app.config['UPLOAD_FOLDER'] = './static/uploads/'

Bootstrap(app)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def rgb_to_hex(clrs):
    hexs = []
    for color in clrs:
        tmphex = "#"
        for val in color.rgb:
            val = hex(val)
            if len(val) != 4:
                tmphex+="0"
            tmphex+= (str(val).replace("0x","").upper())
        hexs.append(tmphex)
    return hexs

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

            clrs = colorgram.extract(file,10)
            hexs = rgb_to_hex(clrs)
            return render_template('index.html', form=form, path=path,clrs=hexs)
            
        else:
            flash("File not allowed")
            return redirect(url_for('home'))
    return render_template('index.html',form=form)

if __name__ == "__main__":
    app.run(debug=True)