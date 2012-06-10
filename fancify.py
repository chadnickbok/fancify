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
        cur_request = """{"url": "http://www.viewzone.com/attractive.female.jpg", "debug":true}"""
        cur_request = json.loads(cur_request)

    print cur_request["url"]
    img = Image(str(cur_request["url"]))

    debug = False
    if "debug" in cur_request:
        debug = cur_request["debug"]

    faces = img.findHaarFeatures(face_cascade)
    if faces is not None:
        for face in faces:
            nose = None
            mouth = None
            cur_face = face.crop()
            noses = cur_face.findHaarFeatures(nose_cascade)
            mouths = cur_face.findHaarFeatures(mouth_cascade)
            eyes = cur_face.findHaarFeatures(eye_cascade)
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
                right_eye = eyes[0]
                left_eye = eyes[0]
                right_eye_dist = abs(face_left_edge + right_eye.x - (face.x + (face.width() / 4))) + abs(face_top_edge + right_eye.y - (face.y - (face.height() / 4)))
                left_eye_dist = abs(face_left_edge + left_eye.x - (face.x - (face.width() / 4))) + abs(face_top_edge + left_eye.y - (face.y - (face.height() / 4)))
                for cur_eye in eyes:
                    cur_right_dist = abs(face_left_edge + cur_eye.x - (face.x + (face.width() / 4))) + abs(face_top_edge + cur_eye.y - (face.y - (face.height() / 4)))
                    cur_left_dist = abs(face_left_edge + cur_eye.x - (face.x - (face.width() / 4))) + abs(face_top_edge + cur_eye.y - (face.y - (face.height() / 4)))

                    if cur_right_dist < right_eye_dist:
                        right_eye = cur_eye
                        right_eye_dist = cur_right_dist

                    if cur_left_dist < left_eye_dist:
                        left_eye = cur_eye
                        left_eye_dist = cur_left_dist

            if nose and mouth:

                x_face = face.x - (face.width() / 2)
                y_face = face.y - (face.height() / 2)

                x_nose = nose.x - (nose.width() / 2)
                y_nose = nose.y - (nose.height() / 2)

                x_mouth = mouth.x - (mouth.width() / 2)
                y_mouth = mouth.y - (mouth.height() / 2)

                x_right_eye = right_eye.x - (right_eye.width() / 2)
                y_right_eye = right_eye.y - (right_eye.height() / 2)

                # Setup Mustache Image
                cur_stache = stache.copy()
                scale_factor = nose.width() / 300.0
                cur_stache = cur_stache.scale(scale_factor)
                stache_mask = cur_stache.createAlphaMask(hue_lb=0, hue_ub=10).invert()

                #calculate the mustache position
                bottom_of_nose = y_nose + (nose.height() * 3 / 4)
                top_of_mouth = y_mouth
                y_must = y_face + ((bottom_of_nose + top_of_mouth) / 2) - (cur_stache.height / 2)

                middle_of_nose = nose.x
                middle_of_mouth = mouth.x
                x_must = x_face + ((middle_of_nose + middle_of_mouth) / 2) - (cur_stache.width / 2)

                # Setup Monocle Image
                cur_mono = monocle.copy()
                scale_factor = right_eye.width() / 65.0
                cur_mono = cur_mono.scale(scale_factor)
                mono_mask = cur_mono.createAlphaMask(hue_lb=0, hue_ub=100).invert()

                # Calculate Monocle Position
                x_mono = x_face + x_right_eye
                y_mono = y_face + y_right_eye

                img = img.blit(cur_stache, pos=(x_must, y_must), alphaMask=stache_mask)
                img = img.blit(cur_mono, pos=(x_mono, y_mono), alphaMask=mono_mask)

                if debug:
                    face_left_edge = face.x - (face.width() / 2)
                    face_top_edge = face.y - (face.height() / 2)

                    facelayer = DrawingLayer((img.width, img.height))
                    facebox_dimensions = (face.width(), face.height())
                    center_point = (face.x, face.y)
                    facebox = facelayer.centeredRectangle(center_point, facebox_dimensions)
                    img.addDrawingLayer(facelayer)

                    noselayer = DrawingLayer((img.width, img.height))
                    nosebox_dimensions = (nose.width(), nose.height())
                    center_point = (face.x - (face.width() / 2) + nose.x,
                                    face.y - (face.height() / 2) + nose.y)
                    nosebox = noselayer.centeredRectangle(center_point, nosebox_dimensions)
                    img.addDrawingLayer(noselayer)

                    mouthlayer = DrawingLayer((img.width, img.height))
                    mouthbox_dimensions = (mouth.width(), mouth.height())
                    center_point = (face.x - (face.width() / 2) + mouth.x,
                                face.y - (face.height() / 2) + mouth.y)
                    mouthbox = mouthlayer.centeredRectangle(center_point, mouthbox_dimensions)
                    img.addDrawingLayer(mouthlayer)

                    right_eyelayer = DrawingLayer((img.width, img.height))
                    right_eyebox_dimensions = (right_eye.width(), right_eye.height())
                    right_eye_center_point = (face_left_edge + right_eye.x, face_top_edge + right_eye.y)
                    right_eyebox = right_eyelayer.centeredRectangle(right_eye_center_point, right_eyebox_dimensions)
                    img.addDrawingLayer(right_eyelayer)

                    img = img.applyLayers()

    output = StringIO.StringIO()
    img.getPIL().save(output, format="JPEG")
    img_contents = output.getvalue()

    mimetype = "image/jpeg"
    return app.response_class(img_contents, mimetype=mimetype, direct_passthrough=False)

if __name__ == '__main__':
    app.run()
