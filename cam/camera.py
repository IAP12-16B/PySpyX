# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import psutil

from cam.surveillance import Surveillance


try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import subprocess
from PIL import Image
import netifaces
import socket

"""
Camera Surveillance tool for Raspberry Pi with Camera module Project in ICT M152.
Copyright (C) 2015  Kim D. Jeker

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = 'kije'

def isReachable(ip, port, timeout=5):
    """
    :param ip: string
    :param port: int
    :param timeout: float
    :return:
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.settimeout(timeout)
            s.connect((ip, port))
            return True
        except socket.error as e:
            # todo maybe log
            return False


class Camera:
    CAM_STREAMING_PORT = 8554

    def __init__(self):
        pass

    def getStreamUrl(self):
        """
        :return: string
        """
        return "rtsp://%s:%d" % (self.getIp(), self.CAM_STREAMING_PORT)

    def getIp(self):
        """
        :return: string
        """
        pass

    def isRemote(self):
        """
        :return: boolean
        """
        pass

    def isStreamReachable(self):
        """
        Check if the stream is reachable
        :return: boolean
        """
        return self.isReachable(self.CAM_STREAMING_PORT)

    def isReachable(self, port, timeout=1):
        """
        returns if a port is reachable. result will be cached
        :param port: int
        :param timeout: float
        :return: boolean
        """
        return isReachable(self.getIp(), port, timeout)


class LocalCamera(Camera):
    """
    @type surveillance: Surveillance
    """
    CAM_CAPTURE_PHOTO_CMD = "raspistill"
    CAM_CAPTURE_VIDEO_CMD = "raspivid"
    CAM_VLC_CMD = "cvlc"
    CAM_MOTION_CMD = "motion"

    def __init__(self):
        super().__init__()
        self.surveillance = Surveillance(self)

    def captureVideo(self, path, length=15000, width=None, height=None):
        """
        :param path: string
        :param length: int length in milliseconds
        :param width: int|None
        :param height: int|None
        :return: boolean
        :raise: subprocess.CalledProcessError:
        """
        return subprocess.check_call(
            self.__getVideoCmd__(path=path, length=length, width=width, height=height),
            shell=True
        )

    def __getVideoCmd__(self, path="-", length=15000, width=None, height=None, fps=None):
        """
        :param path: string
        :param length: int length in milliseconds
        :param width: int|None
        :param height: int|None
        :return: string
        """
        return "%s -t %d %s %s %s -o %s -n" % (
            self.CAM_CAPTURE_VIDEO_CMD,
            length,
            "-w %s" % width if width is not None else "",
            "-h %s" % height if width is not None else "",
            "-fps %d" % fps if fps is not None else "",
            path  # todo make sure path is not malicious
        )

    def getImage(self):
        """
        :return: PIL.Image.Image
        :raises subprocess.CalledProcessError:
        """
        return self.__getImage__()

    def getThumbnailImage(self):
        """
        :return: PIL.Image.Image
        :raises subprocess.CalledProcessError:
        """
        return self.__getImage__(200, 150)

    def __getImage__(self, width=None, height=None):
        """
        :param width: int | None
        :param height: int | None
        :return: PIL.Image.Image
        :raises subprocess.CalledProcessError:
        """
        imageData = StringIO()
        imageData.write(subprocess.check_output(self.__getImageCmd__(width=width, height=height), shell=True))
        imageData.seek(0)
        im = Image.open(imageData)
        imageData.close()
        return im

    def __getImageCmd__(self, width=None, height=None):
        """
        :param width: int | None
        :param height: int | None
        :return:
        """
        return "%s %s %s -t 0 -e bmp -o -" % (
            self.CAM_CAPTURE_PHOTO_CMD,
            "-w %s" % width if width is not None else "",
            "-h %s" % height if width is not None else "",
        )

    def getIp(self):
        """
        :return: string
        """
        interfaces = netifaces.interfaces()
        for i in interfaces:
            if i.startswith('lo'):
                continue

            iface = netifaces.ifaddresses(i).get(netifaces.AF_INET)
            if iface != None:
                for j in iface:
                    return j['addr']

    def isRemote(self):
        """
        :return: boolean
        """
        return False

    def isReachable(self, port, timeout=0.2):
        """
        returns if a port is reachable. result will be cached
        :param port: int
        :param timeout: float
        :return: boolean
        """
        return isReachable('127.0.0.1', port, timeout)  # faster & up to date value

    def startStreaming(self, width=1200, height=800, fps=15):
        """
        Starts the stream (if not already started)
        :param width: int
        :param height: int
        :param fps: int
        """
        if not self.isStreamOn():
            subprocess.Popen(
                self.__getStreamingCmd__(width=width, height=height),
                shell=True
            )

    def __getStreamingCmd__(self, width=1200, height=800, fps=15):
        """

        :param width: int
        :param height: int
        :param fps: int
        :return: string
        """
        return "%s | %s -vvv stream:///dev/stdin --sout '#rtp{sdp=rtsp://:%d/}' :demux=h264" % (
            self.__getVideoCmd__(path="-", length=0, width=width, height=height, fps=fps),
            self.CAM_VLC_CMD,
            self.CAM_STREAMING_PORT
        )


    def stopStreaming(self):
        """
        Stops the stream (if started)
        """
        if self.isStreamOn():
            return subprocess.check_call(
                "killall %s %s" % (self.CAM_CAPTURE_VIDEO_CMD, self.CAM_VLC_CMD),
                shell=True
            )

    def startSurveillance(self):
        """
        Starts the surveillance mode (if not already started)
        """
        if not self.isSurveillanceOn():
            pass  # todo

    def stopSurveillance(self):
        """
        Stops the surveillance mode (if started)
        """
        if self.isSurveillanceOn():
            return subprocess.check_call(
                "killall %s" % self.CAM_MOTION_CMD,
                shell=True
            )

    def stopAll(self):
        """
        Stops every activity (streaming, surveillance). Turns the camera "off"
        """
        self.stopSurveillance()
        self.stopStreaming()

    def isSurveillanceOn(self):
        """
        Check if surveillance mode is on
        :return: boolean
        """
        # check, if motion process is running
        for p in psutil.process_iter():
            try:
                p.exe().lower().index(self.CAM_MOTION_CMD)
                return True
            except ValueError:
                pass
            except psutil.AccessDenied:
                pass

        return False

    def isStreamOn(self):
        """
        Check if stream is started
        :return: boolean
        """
        # check, if streaming process is running
        for p in psutil.process_iter():
            try:
                p.exe().lower().index(self.CAM_VLC_CMD)

                return True
            except ValueError:
                pass
            except psutil.AccessDenied:
                pass

        return False
        # return self.isStreamReachable()



class RemoteCamera(Camera):
    """
    @type camera: pyspy.models.Camera
    """

    def __init__(self, camera):
        """
        :param camera: pyspy.models.Camera
        """
        super().__init__()
        self.camera = camera


    def getIp(self):
        """
        :return: string
        """
        return self.camera.ip

    def isRemote(self):
        """
        :return: boolean
        """
        return True
