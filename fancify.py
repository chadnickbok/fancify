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

import pygame
from pygame import Rect

app = Flask(__name__)
app.debug = True

face_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/face.xml")
nose_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/nose.xml")
mouth_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/mouth.xml")
eye_cascade = HaarCascade("/var/lib/SimpleCV/Features/HaarCascades/eye.xml")

stache = Image("./new_stache.png")
monocle = Image("./monocle.png")
hat = Image("./top_hat.png")

@app.route('/')
def hello_world():
    return "Hello World!"

@app.route('/fancify', methods=['GET', 'POST'])
def fancify():
    if request.method == 'POST':
        print request.data
        cur_request = json.loads(request.data)
    else:
        #cur_request = """{"url": "", "debug":true}"""
        cur_request = """{"url": "http://collider.com/uploads/imageGallery/Scrubs/scrubs_cast_image__medium_.jpg", "debug":false}"""
        #cur_request = """{"url": "http://localhost/Kevin_Bacon_at_the_2010_SAG_Awards.jpg", "debug":false}"""
        #cur_request = """{"url": "http://cdn02.cdn.justjared.com/wp-content/uploads/headlines/2012/02/anna-faris-oscars-red-carpet-2012.jpg", "debug":true}"""
        #cur_request = """{"url": "http://www.viewzone.com/attractive.female.jpg", "debug":true}"""
        cur_request = json.loads(cur_request)

    print cur_request["url"]
    img = Image(str(cur_request["url"]))
    img = img.scale(2.0)

    debug = False
    if "debug" in cur_request:
        debug = cur_request["debug"]

    chosen_faces = []
    faces = img.findHaarFeatures(face_cascade)
    if faces is not None:
        for face in faces:
            invalid_face = False
            face_rect = Rect(face.x - (face.width() / 2), face.y - (face.height() / 2), face.width(), face.height())
            for chosen_face in chosen_faces:
                if face_rect.colliderect(chosen_face):
                    invalid_face = True
                    break
            if invalid_face:
                break

            nose = None
            mouth = None
            left_eye = None
            right_eye = None
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

            if nose and mouths is not None:
                mouth = mouths[0]
                mouth_dist = abs(mouth.x - nose.x) + (abs(mouth.y - (face.height() * 4 / 5)) * 2)

                for cur_mouth in mouths:
                    cur_dist = abs(cur_mouth.x - nose.x) + (abs(cur_mouth.y - (face.height() * 4/ 5)) * 2)
                    if cur_dist < mouth_dist:
                        mouth = cur_mouth
                        mouth_dist = cur_dist

            if nose and eyes is not None:
                right_eye = eyes[0]
                left_eye = eyes[0]
                right_eye_dist = abs(right_eye.x - (3 * face.width() / 4)) + abs(right_eye.y - (nose.y + (face.height() / 4) / 2))
                left_eye_dist = abs(face_left_edge + left_eye.x - (face.x - (face.width() / 4))) + abs(face_top_edge + left_eye.y - (face.y - (face.height() / 5))) / 2
                for cur_eye in eyes:
                    cur_right_dist = abs(cur_eye.x - (3 * face.width() / 4)) + abs(cur_eye.y - (nose.y + (face.height() / 4) / 2))
                    cur_left_dist = abs(face_left_edge + cur_eye.x - (face.x - (face.width() / 4))) + abs(face_top_edge + cur_eye.y - (face.y - (face.height() / 5))) / 2

                    if (cur_right_dist < right_eye_dist) and (cur_eye.x > (nose.x)):
                        right_eye = cur_eye
                        right_eye_dist = cur_right_dist

                    if (cur_left_dist < left_eye_dist) and (cur_eye.x < (face.width() / 2)):
                        left_eye = cur_eye
                        left_eye_dist = cur_left_dist

            if right_eye and (right_eye.x < (face.width() / 2)):
                right_eye = None

            if nose and mouth and right_eye:
                chosen_faces.append(face_rect)
                x_face = face.x - (face.width() / 2)
                y_face = face.y - (face.height() / 2)

                x_nose = nose.x - (nose.width() / 2)
                y_nose = nose.y - (nose.height() / 2)

                x_mouth = mouth.x - (mouth.width() / 2)
                y_mouth = mouth.y - (mouth.height() / 2)

                x_right_eye = right_eye.x - (right_eye.width() / 2)
                y_right_eye = right_eye.y - (right_eye.height() / 2)

                # Setup TopHat Image
                cur_hat = hat.copy()
                scale_factor = face.width() / 350.0
                cur_hat = cur_hat.scale(scale_factor)
                hat_mask = cur_hat.createAlphaMask(hue_lb=0, hue_ub=3).invert()

                # Calculate the hat position
                if (face.y - face.height() / 2) > cur_hat.height:
                    x_hat = face.x - (cur_hat.width / 2)
                    y_hat = face.y - (face.height() * 4 / 5) - (cur_hat.height / 2)
                    img = img.blit(cur_hat, pos=(x_hat, y_hat), alphaMask=hat_mask)

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
                scale_factor = ((right_eye.width() / 65.0) + (face.width() / 200.0)) / 2.0
                cur_mono = cur_mono.scale(scale_factor)
                mono_mask = cur_mono.createAlphaMask(hue_lb=0, hue_ub=100).invert()

                # Calculate Monocle Position
                x_mono = x_face + x_right_eye
                y_mono = y_face + y_right_eye

                img = img.blit(cur_stache, pos=(x_must, y_must), alphaMask=stache_mask)
                img = img.blit(cur_mono, pos=(x_mono, y_mono), alphaMask=mono_mask)

                if debug:
                    noselayer = DrawingLayer((img.width, img.height))
                    nosebox_dimensions = (nose.width(), nose.height())
                    center_point = (face.x - (face.width() / 2) + nose.x,
                                    face.y - (face.height() / 2) + nose.y)
                    nosebox = noselayer.centeredRectangle(center_point, nosebox_dimensions, width=3)
                    img.addDrawingLayer(noselayer)
                    img = img.applyLayers()



            if debug:
                face_left_edge = face.x - (face.width() / 2)
                face_top_edge = face.y - (face.height() / 2)

                facelayer = DrawingLayer((img.width, img.height))
                facebox_dimensions = (face.width(), face.height())
                center_point = (face.x, face.y)
                facebox = facelayer.centeredRectangle(center_point, facebox_dimensions, Color.BLUE)
                img.addDrawingLayer(facelayer)

                if noses:
                    for nose in noses:
                        noselayer = DrawingLayer((img.width, img.height))
                        nosebox_dimensions = (nose.width(), nose.height())
                        center_point = (face.x - (face.width() / 2) + nose.x,
                                    face.y - (face.height() / 2) + nose.y)
                        nosebox = noselayer.centeredRectangle(center_point, nosebox_dimensions)
                        img.addDrawingLayer(noselayer)
                else:
                    print "No noses"

                if mouths:
                    for mouth in mouths:
                        mouthlayer = DrawingLayer((img.width, img.height))
                        mouthbox_dimensions = (mouth.width(), mouth.height())
                        center_point = (face.x - (face.width() / 2) + mouth.x,
                                face.y - (face.height() / 2) + mouth.y)
                        mouthbox = mouthlayer.centeredRectangle(center_point, mouthbox_dimensions)
                        img.addDrawingLayer(mouthlayer)
                else:
                    print "No mouths"

                if eyes:
                    for right_eye in eyes:
                        right_eyelayer = DrawingLayer((img.width, img.height))
                        right_eyebox_dimensions = (right_eye.width(), right_eye.height())
                        right_eye_center_point = (face_left_edge + right_eye.x, face_top_edge + right_eye.y)
                        right_eyebox = right_eyelayer.centeredRectangle(right_eye_center_point, right_eyebox_dimensions)
                        img.addDrawingLayer(right_eyelayer)
                else:
                    print "No eyes"

                img = img.applyLayers()

    img = img.scale(0.5)
    w_ratio = img.width / 800.0
    h_ratio = img.height / 600.0

    if h_ratio > 1.0 and w_ratio > 1.0:
        if h_ratio > w_ratio:
            print "Resizing to height 600"
            img = img.resize(h=600)
        else:
            print "Resizing to width 800"
            img = img.resize(w=800)

    output = StringIO.StringIO()
    img.getPIL().save(output, format="JPEG", quality=85, optimize=True)
    img_contents = output.getvalue()

    mimetype = "image/jpeg"
    return app.response_class(img_contents, mimetype=mimetype, direct_passthrough=False)

if __name__ == '__main__':
    app.run()
