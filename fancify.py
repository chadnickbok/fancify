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
from SimpleCV import DrawingLayer

import rsvg
import cairo
import array

app = Flask(__name__)
app.debug = True

face_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/face.xml")
nose_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/nose.xml")
mouth_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/mouth.xml")
eye_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/eye.xml")

stache = Image("./new_stache.png")
monocle = Image("./monocle.png")

@app.route('/')
def hello_world():
    return "Hello World!"

@app.route('/fancify', methods=['GET', 'POST'])
def fancify():
    if request.method == 'POST':
        print request.data
        cur_request = json.loads(request.data)
    else:
        cur_request = """{"url": "http://www.viewzone.com/attractive.female.jpg"}"""
        cur_request = json.loads(cur_request)

    print cur_request["url"]
    img = Image(str(cur_request["url"]))
    faces = img.findHaarFeatures(face_cascade)
    if faces is not None:
        for face in faces:
            nose = None
            mouth = None
            cur_face = face.crop()
            noses = cur_face.findHaarFeatures(nose_cascade)
            mouths = cur_face.findHaarFeatures(mouth_cascade)
            eyes = cur_face.findHaarFeatures(eye_cascade)
            print "X:", face.x
            print "Y:", face.y
            face_left_edge = face.x - (face.width() / 2)
            face_top_edge = face.y - (face.height() / 2)

            if noses is not None:
                nose = noses[0]
                nose_dist = abs(face_left_edge + nose.x - face.x) + abs(face_top_edge + nose.y - face.y)
                for cur_nose in noses:
                    cur_dist = abs(face_left_edge + cur_nose.x - face.x) + abs(face_top_edge + cur_nose.y - face.y)
                    if cur_dist < nose_dist:
                        nose = cur_nose
                        nost_dist = cur_dist

            if mouths is not None:
                mouth = mouths[0]
                mouth_dist = abs(face_left_edge + mouth.x - face.x) + abs(face_top_edge + mouth.y - (face.y + (face.height() / 4)))
                for cur_mouth in mouths:
                    cur_dist = abs(cur_mouth.x - face.x) + abs(cur_mouth.y - (face.y + (face.height() / 4)))
                    if cur_dist < mouth_dist:
                        mouth = cur_mouth
                        mouth_dist = cur_dist

            if eyes is not None:
                eye = eyes[0]
                eye_dist = abs(face_left_edge + eye.x - (face.x + (face.width() / 4))) + abs(face_top_edge + eye.y - (face.y - (face.height() / 4)))
                for cur_eye in eyes:
                    cur_dist = abs(face_left_edge + cur_eye.x - (face.x + (face.width() / 4))) + abs(face_top_edge + cur_eye.y - (face.y - (face.height() / 4)))
                    if cur_dist < eye_dist:
                        eye = cur_eye
                        eye_dist = cur_dist

            if nose and mouth:

                x_face = face.x - (face.width() / 2)
                y_face = face.y - (face.height() / 2)

                x_nose = nose.x - (nose.width() / 2)
                y_nose = nose.y - (nose.height() / 2)

                x_mouth = mouth.x - (mouth.width() / 2)
                y_mouth = mouth.y - (mouth.height() / 2)

                x_eye = eye.x - (eye.width() / 2)
                y_eye = eye.y - (eye.height() / 2)

                #blit the stache/mask onto the image
                cur_stache = stache.copy()
                scale_factor = nose.width() / 300.0
                cur_stache = cur_stache.scale(scale_factor)
                stache_mask = cur_stache.createAlphaMask(hue_lb=0, hue_ub=10).invert()

                #calculate the mustache position
                x_must = x_face + x_mouth + (mouth.width() / 2) - (cur_stache.width / 2)
                y_must = y_face + y_mouth - (cur_stache.height / 2)

                # Scale the monocle
                cur_mono = monocle.copy()
                scale_factor = eye.width() / 65.0
                cur_mono = cur_mono.scale(scale_factor)
                mono_mask = cur_mono.createAlphaMask(hue_lb=0, hue_ub=100).invert()

                x_mono = x_face + x_eye + (eye.width() / 2) - (cur_mono.width / 3)
                y_mono = y_face + y_eye + (eye.height() / 2) - (cur_mono.width / 2)

                facelayer = DrawingLayer((img.width, img.height))
                facebox_dimensions = (face.width(), face.height())
                center_point = (face.x, face.y)
                facebox = facelayer.centeredRectangle(center_point, facebox_dimensions)
                #img.addDrawingLayer(facelayer)

                noselayer = DrawingLayer((img.width, img.height))
                nosebox_dimensions = (nose.width(), nose.height())
                center_point = (face.x - (face.width() / 2) + nose.x,
                                    face.y - (face.height() / 2) + nose.y)
                nosebox = noselayer.centeredRectangle(center_point, nosebox_dimensions)
                #img.addDrawingLayer(noselayer)

                mouthlayer = DrawingLayer((img.width, img.height))
                mouthbox_dimensions = (mouth.width(), mouth.height())
                center_point = (face.x - (face.width() / 2) + mouth.x,
                                face.y - (face.height() / 2) + mouth.y)
                mouthbox = mouthlayer.centeredRectangle(center_point, mouthbox_dimensions)
                #img.addDrawingLayer(mouthlayer)

                #img = img.applyLayers()
                img = img.blit(cur_stache, pos=(x_must, y_must), alphaMask=stache_mask)
                img = img.blit(cur_mono, pos=(x_mono, y_mono), alphaMask=mono_mask)

    output = StringIO.StringIO()
    img.getPIL().save(output, format="JPEG")
    img_contents = output.getvalue()

    mimetype = "image/jpeg"
    return app.response_class(img_contents, mimetype=mimetype, direct_passthrough=False)

if __name__ == '__main__':
    app.run()
