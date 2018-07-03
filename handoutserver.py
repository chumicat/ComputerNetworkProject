import io
import socket
import struct
import time
import datetime
import PIL
from PIL import Image
import numpy
import logging
import socketserver
from threading import Condition
from http import server
from threading import Thread
from socketServer import ThreadingMixIn
import cv2
import random


randomseed = int(random.random() * 5)

# global variable
clientimage = []
framesize = (320, 240)
white = [255, 255, 255]
threshold = 4

#main process in this function
def imgprocess(img, thrid, cleimg):
    # img = cv2_filter(img, randomseed)
    if len(cleimg) < thrid + 1:
        cleimg.append(img)
    else:
        cleimg[thrid] = img
    if len(cleimg) == 1:
        return mergeimg(cleimg[0], whiteimg(framesize)), cleimg
    elif len(cleimg) == 2:
        if thrid == 0:
            return mergeimg(cleimg[1], whiteimg(framesize)), cleimg
        else:
            return mergeimg(cleimg[0], whiteimg(framesize)), cleimg
    elif len(cleimg) == 3:
        if thrid == 0:
            return mergeimg(cleimg[1], cleimg[2]), cleimg
        elif thrid == 1:
            return mergeimg(cleimg[2], cleimg[0]), cleimg
        else:
            return mergeimg(cleimg[0], cleimg[1]), cleimg
    else:
        return [], []

def mergeimg(img1, img2):
    return numpy.concatenate((img1, img2), axis = 1)

def whiteimg(size):
    return [ [white for i in range(size[0])] for i in range(size[1])]

def getid(x):
    for i in range(len(x)):
        if not x[i].active:
            return i
    return -1


class ClientThread(Thread):
    def __init__(self, conn, ip, port):
        Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port
        self.active = True
        self.id = -1

    def run(self):
        self.connection = conn.makefile('wrb')
        try:
            while True:
                if not self.active:
                    break

                image_len = struct.unpack('<L', self.connection.read(struct.calcsize('<L')))[0]
                print(image_len)
                if not image_len:
                    break
                img = self.connection.read(image_len)

                image_stream = io.BytesIO()
                # read photo
                image_stream.write(img)

                image_stream.seek(0)
                image = Image.open(image_stream)
                global framesize
                framesize = image.size
                global clientimage
                image, clientimage = imgprocess(numpy.array(image), self.id, clientimage)
                img = cv2.imencode('.jpg', image)[1].tostring()

                s = struct.pack('<L', len(img))
                # transform length to server
                self.connection.write(s)
                self.connection.flush()
                # transform photo stream to server
                self.connection.write(img)
                self.connection.flush()
        except Exception as e:
            print(e)
            self.connection.close()
            self.active = False
            exit(1)
        finally:
            self.connection.close()

server_socket = socket.socket()
server_socket.bind(('127.0.0.1', 8002))

client_threads = []

while True:
    server_socket.listen(2)
    (conn, (ip, port)) = server_socket.accept()
    if len(client_threads) < 3:
        newthread = ClientThread(conn, ip, port)
        newthread.start()
        newthread.id = len(client_threads)
        client_threads.append(newthread)
    else:
        thrid = getid(client_threads)
        if thrid >= 0:
            newthread = ClientThread(conn, ip, port)
            newthread.start()
            newthread.id = thrid
            client_threads[thrid] = newthread

