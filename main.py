from flask import Flask
from flask import render_template
from flask import request

from brew_support import HomebrewPkg

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/homebrew/<package>")
def packages(package):
    try:
        pkg = HomebrewPkg(package)
    except Exception as e:
        return "<h1>Error fetching package</h1>"
    else:
        return render_template("brew.html", data=pkg)


