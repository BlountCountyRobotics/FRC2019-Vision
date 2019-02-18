#!/usr/bin/env python3
#----------------------------------------------------------------------------
# Copyright (c) 2018 FIRST. All Rights Reserved.
# Open Source Software - may be modified and shared by FRC teams. The code
# must be accompanied by the FIRST BSD license file in the root directory of
# the project.
#----------------------------------------------------------------------------

import json
import time
import sys

from cscore import CameraServer, VideoSource, UsbCamera, MjpegServer, CvSource
import cscore
import numpy
from networktables import NetworkTablesInstance, NetworkTables
import pixy
import cv2


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
#               "properties": [                          // optional
#                   {
#                       "name": <property name>
#                       "value": <property value>
#                   }
#               ],
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
    if config.pixy:
        global pixy_source
        pixy_source = inst.putVideo("Pixy", 51, 51)

        #camera.setConfigJson(json.dumps(config.config))
        #camera.setConnectionStrategy(VideoSource.ConnectionStrategy.kKeepOpen)
    else:
        camera = UsbCamera(config.name, config.path)
        server = inst.startAutomaticCapture(camera=camera, return_server=True)

        camera.setConfigJson(json.dumps(config.config))
        camera.setConnectionStrategy(VideoSource.ConnectionStrategy.kKeepOpen)

    if config.streamConfig is not None and config.pixy is False:
        server.setConfigJson(json.dumps(config.streamConfig))

    return camera

def initialize():
    pixy.init()
    #pixy.change_prog("line")

def get_pixy_image():
    pixy.line_get_all_features()
    pixy.line_get_vectors(1, vectors)

    image = numpy.zeros((51, 51, 1), dtype=numpy.uint8)
    cv2.line(image, (vectors[0].m_y0,vectors[0].m_x0), (vectors[0].m_y1, vectors[0].m_x1), 256, thickness=5)
    return image

if __name__ == "__main__":
    global pixy_sources
    if len(sys.argv) >= 2:
        configFile = sys.argv[1]

    # read configuration
    if not readConfig():
        sys.exit(1)

    # start NetworkTables
    ntinst = NetworkTablesInstance.getDefault()
    NetworkTables.initialize(server='roborio-4504-frc.local')
    sd = NetworkTables.getTable('SmartDashboard')


    if server:
        ntinst.startServer()
    else:
        ntinst.startClientTeam(team)

    # start cameras
    cameras = []
    for cameraConfig in cameraConfigs:
        cameras.append(startCamera(cameraConfig))
    initialize()
    # loop forever
    while True:
        image = get_pixy_image()
        pixy_source.putFrame(image)
        sd.putNumber("y0",vectors[0].m_y0)
        sd.putNumber("x0",vectors[0].m_x0)
        sd.putNumber("y1",vectors[0].m_y1)
        sd.putNumber("x1",vectors[0].m_x1)
        sd.putNumber("error", ((vectors[0].m_x0 + vectors[0].m_x1)/2) - 36)
