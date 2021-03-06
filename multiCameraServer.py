#!/usr/bin/env python3
#----------------------------------------------------------------------------
# Copyright (c) 2018 FIRST. All Rights Reserved.
# Open Source Software - may be modified and shared by FRC teams. The code
# must be accompanied by the FIRST BSD license file in the root directory of
# the project.
#----------------------------------------------------------------------------

import json, time, sys, cscore, numpy, pixy, cv2
from cscore import CameraServer, VideoSource, UsbCamera, MjpegServer, CvSource
from networktables import NetworkTablesInstance, NetworkTables

#-------------------------------------------------------------------------------------

#____________/\\\______/\\\\\\\\\\\\\\\______/\\\\\\\_______________/\\\____
# __________/\\\\\_____\/\\\///////////_____/\\\/////\\\___________/\\\\\____
#  ________/\\\/\\\_____\/\\\_______________/\\\____\//\\\________/\\\/\\\____
#   ______/\\\/\/\\\_____\/\\\\\\\\\\\\_____\/\\\_____\/\\\______/\\\/\/\\\____
#    ____/\\\/__\/\\\_____\////////////\\\___\/\\\_____\/\\\____/\\\/__\/\\\____
#     __/\\\\\\\\\\\\\\\\_____________\//\\\__\/\\\_____\/\\\__/\\\\\\\\\\\\\\\\_
#      _\///////////\\\//___/\\\________\/\\\__\//\\\____/\\\__\///////////\\\//__
#       ___________\/\\\____\//\\\\\\\\\\\\\/____\///\\\\\\\/_____________\/\\\____
#        ___________\///______\/////////////________\///////_______________\///_____
# Welcome to Team 4504's offboard vision code the raspberry pi.

# Contributors:
# porgull/Connor Barker

#-------------------------------------------------------------------------------------

#   JSON format:
#   {
#       "team": <team number>,
#       "ntmode": <"client" or "server", "client" if unspecified>
#       "cameras": [
#           {
#               "name": <camera name>
#               "path": <path, e.g. "/dev/video0">
#               "pixel format": <"MJPEG", "YUYV", etc>   // optional
#               "width": <video mode width>              // optional
#               "height": <video mode height>            // optional
#               "fps": <video mode fps>                  // optional
#               "brightness": <percentage brightness>    // optional
#               "white balance": <"auto", "hold", value> // optional
#               "exposure": <"auto", "hold", value>      // optional
#               "pixy": <is cam pixy>
#               "stream": {                              // optional
#                   "properties": [
#                       {
#                           "name": <stream property name>
#                           "value": <stream property value>
#                       }
#                   ]
#               }
#           }
#       ]
#   }

#-------------------------------------------------------------------------------------

# MOST CODE IS UNEDITED FROM THE EXAMPLE:

configFile = "/boot/frc.json"

class CameraConfig: pass

team = 4504
server = False
cameraConfigs = []
pixy_source = None
vectors = pixy.VectorArray(1)


"""Report parse error."""
def parseError(str):
    print("config error in '" + configFile + "': " + str, file=sys.stderr)

"""Read single camera configuration."""
def readCameraConfig(config):
    cam = CameraConfig()

    # name
    try:
        cam.name = config["name"]
    except KeyError:
        parseError("could not read camera name")
        return False

    # path
    try:
        cam.path = config["path"]
    except KeyError:
        parseError("camera '{}': could not read path".format(cam.name))
        return False


    #ADDED CODE: add pixy as a camera property
    try:
        cam.pixy = config["pixy"]
    except KeyError:
        parseError("camera '{}': could not read pixy".format(came.name))

    # stream properties
    cam.streamConfig = config.get("stream")

    cam.config = config

    cameraConfigs.append(cam)
    return True

"""Read configuration file."""
def readConfig():
    global team
    global server

    # parse file
    try:
        with open(configFile, "rt") as f:
            j = json.load(f)
    except OSError as err:
        print("could not open '{}': {}".format(configFile, err), file=sys.stderr)
        return False

    # top level must be an object
    if not isinstance(j, dict):
        parseError("must be JSON object")
        return False

    # team number
    try:
        team = j["team"]
    except KeyError:
        parseError("could not read team number")
        return False

    # ntmode (optional)
    if "ntmode" in j:
        str = j["ntmode"]
        if str.lower() == "client":
            server = False
        elif str.lower() == "server":
            server = True
        else:
            parseError("could not understand ntmode value '{}'".format(str))

    # cameras
    try:
        cameras = j["cameras"]
    except KeyError:
        parseError("could not read cameras")
        return False
    for camera in cameras:
        if not readCameraConfig(camera):
            return False

    return True

"""Start running the camera."""
def startCamera(config):
    print("Starting camera '{}' on {}".format(config.name, config.path))
    inst = CameraServer.getInstance()
    camera = None
    server = None


    #ADDED CODE: handle pixy camera capture by creating a cvsource, otherwise normal
    if config.pixy:
        #if the camera is a pixy, get a CvSource to put the generated images in
        global pixy_source
        pixy_source = inst.putVideo("Pixy", 51, 51)
    else:
        #if the camera is not a pixy, automatically capture it
        camera = UsbCamera(config.name, config.path)
        server = inst.startAutomaticCapture(camera=camera, return_server=True)

        camera.setConfigJson(json.dumps(config.config))
        camera.setConnectionStrategy(VideoSource.ConnectionStrategy.kKeepOpen)

    if config.streamConfig is not None and config.pixy is False:
        server.setConfigJson(json.dumps(config.streamConfig))

    return camera

#-------------------------------------------------------------------------------------
#ADDED CODE: Initialize and generate pixy images

def initialize():
    #initiliaze the pixy in the module
    pixy.init()
    #ensure it is switched to detect the tape on the ground
    pixy.change_prog("line")

def get_pixy_image():
    #get the vector and put it to the VectorArray
    pixy.line_get_all_features()
    pixy.line_get_vectors(1, vectors)

    #create a black image and add the line
    image = numpy.zeros((51, 51, 1), dtype=numpy.uint8)
    cv2.line(image, (vectors[0].m_y0,vectors[0].m_x0), (vectors[0].m_y1, vectors[0].m_x1), 256, thickness=5)
    return image

#-------------------------------------------------------------------------------------

if __name__ == "__main__":
    global pixy_sources
    if len(sys.argv) >= 2:
        configFile = sys.argv[1]

    # read configuration
    if not readConfig():
        sys.exit(1)

    # start NetworkTables
    ntinst = NetworkTablesInstance.getDefault()
    ntinst.startClientTeam(team)

    #ADDED: get the SmartDashboard to output to automatically
    #get the SmartDashboard table
    NetworkTables.initialize(server='roborio-4504-frc.local')
    sd = NetworkTables.getTable('SmartDashboard')
    W
    # start cameras
    cameras = []
    for cameraConfig in cameraConfigs:
        cameras.append(startCamera(cameraConfig))

    #initialize the pixy camera
    initialize()

    # loop forever
    while True:
        #ADDED CODE: in the loop, continually get and output values

        #create image from the pixy
        image = get_pixy_image()
        #put the created image to the cameraserver
        pixy_source.putFrame(image)

        #put useful values abt the vector the SmartDashboard
        #both for debug and for PID
        sd.putNumber("y0",vectors[0].m_y0)
        sd.putNumber("x0",vectors[0].m_x0)
        sd.putNumber("y1",vectors[0].m_y1)
        sd.putNumber("x1",vectors[0].m_x1)

        #compute the error for PID
        #error is the midpoint of the line's distance from
        #the center of the robot's motion
        sd.putNumber("error", ((vectors[0].m_x0 + vectors[0].m_x1)/2) - 36)
