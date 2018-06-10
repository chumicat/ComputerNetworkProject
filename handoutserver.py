import io
import socket
import struct
import time
import datetime
from PIL import Image
import numpy
import logging
import socketserver
from threading import Condition
from http import server

server_socket = socket.socket()
server_socket.bind(('127.0.0.1', 8002))
server_socket.listen(3)

connection = server_socket.accept()[0].makefile('r+b')

#main process in this function
def imgprocess(img):
    return img

try:
    while (1):
        image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
        print(image_len)
        if not image_len:
            break
        img = connection.read(image_len)

        img_str = imgprocess(img)
        s = struct.pack('<L', len(img_str))
        # transform length to server
        connection.write(s)
        connection.flush()
        # transform photo stream to server
        connection.write(img_str)
        connection.flush()

except Exception as e:
    print(e)
finally:
    connection.close()
    server_socket.close()
