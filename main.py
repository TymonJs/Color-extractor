from flask import Flask, flash, render_template, redirect, url_for,request
from flask_bootstrap import Bootstrap
from forms import ColorForm
from os import environ,path,listdir,remove
from werkzeug.utils import secure_filename
import colorgram
from random import randint


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png','gif',"svg"}


app = Flask(__name__)
app.config['SECRET_KEY'] = environ.get('secret_key')

app.config['UPLOAD_FOLDER'] = './static/uploads/'

Bootstrap(app)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/",methods=['GET','POST'])
def home():
    for file in listdir(app.config['UPLOAD_FOLDER']):
        if file!='stop.txt':
            remove(app.config["UPLOAD_FOLDER"]+file)
            
    form = ColorForm()
    if request.method == 'POST':

        file = request.files['color']

        if file.filename == '':
            flash("File hasn't been selected")
            return redirect(url_for('home'))

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            uploaded_files = listdir(app.config['UPLOAD_FOLDER'])

            while filename in uploaded_files:
                split = filename.split(".")
                filename = split[0] + f"{randint(0,9)}." + split[1]

            path = app.config['UPLOAD_FOLDER'] + filename

            file.save(path)
            clrs = colorgram.extract(path,10)
            for clr in clrs:
                print(clr.hsl,clr.rgb)
            return render_template('index.html', form=form, path=path,clrs=clrs)
            
        else:
            flash("File not allowed")
            return redirect(url_for('home'))
    return render_template('index.html',form=form)

if __name__ == "__main__":
    app.run(debug=True)