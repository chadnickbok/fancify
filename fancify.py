#!/usr/bin/python
#
# Fancify

import json
import tempfile
import urllib
import time
import StringIO

from flask import Flask
from flask import request

import SimpleCV
from SimpleCV import Color, ColorCurve, Camera, Image, pg, np, HaarCascade
from SimpleCV.Display import Display

app = Flask(__name__)
app.debug = True

face_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/face.xml")
nose_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/nose.xml")
stache = Image("./stache.png")
mask = stache.createAlphaMask(hue_lb=60, hue_ub=130).invert()

@app.route('/')
def hello_world():
    return "Hello World!"

@app.route('/fancify', methods=['GET', 'POST'])
def fancify():
    if request.method == 'POST':
        cur_request = {}
        cur_request["url"] = str(request.form['url'])
    else:
        cur_request = """{"url": "http://www.viewzone.com/attractive.female.jpg"}"""
        cur_request = json.loads(cur_request)

    print cur_request["url"]
    img = Image(str(cur_request["url"]))
    faces = img.findHaarFeatures(face_cascade)
    if faces is not None:
        for face in faces:
            cur_face = face.crop()
            noses = cur_face.findHaarFeatures(nose_cascade)

            if noses is not None:
                noses = noses.sortArea()
                nose = noses[0]

                xf = face.x -(face.width()/2)
                yf = face.y -(face.height()/2)
                xm = nose.x -(nose.width()/2)
                ym = nose.y -(nose.height()/2)
                #calculate the mustache position
                xmust = xf+xm-(stache.width/2)+(nose.width()/2)
                ymust = yf+ym+(2*nose.height()/3)

                #blit the stache/mask onto the image
                img = img.blit(stache, pos=(xmust,ymust), alphaMask=mask)

    output = StringIO.StringIO()
    img.getPIL().save(output, format="JPEG")
    img_contents = output.getvalue()

    mimetype = "image/jpeg"
    return app.response_class(img_contents, mimetype=mimetype, direct_passthrough=False)

if __name__ == '__main__':
    app.run()