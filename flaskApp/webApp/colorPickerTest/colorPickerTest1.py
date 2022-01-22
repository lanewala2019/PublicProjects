from flask import Flask, render_template
# from flask_colorpicker import colorpicker
# Some junk to solve loading module path from parent dir
from sys import path
from os import getcwd, name
splitter = '\\' if name == 'nt' else '/'
path.append(
    splitter.join(
        getcwd().split(
            splitter
        )[:-1]
    )
)
# End of junk
from flask_colorpicker import colorpicker

app=Flask(__name__) #instantiating flask object
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'

colorpicker(app, local=['static/spectrum.js', 'static/spectrum.css'])


@app.route('/')
def home():
    return render_template('index.html')


app.run(host='0.0.0.0', port='5002')