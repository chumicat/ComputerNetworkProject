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
from threading import Thread 
from SocketServer import ThreadingMixIn

#main process in this function
def imgprocess(img):
    return img

class ClientThread(Thread):
    def __init__(self, conn, ip, port):
        Thread.__init__(self)
        self.conn = conn
        self.ip = ip
        self.port = port

    def run(self):
        self.connection = conn.makefile('r+b')
        try:
            while True:
                self.image_len = struct.unpack('<L', self.connection.read(struct.calcsize('<L')))[0]
                print(self.image_len)
                if not self.image_len:
                    break
                self.img = self.connection.read(self.image_len)

                self.img_str = imgprocess(self.img)
                self.s = struct.pack('<L', len(self.img_str))
                # transform length to server
                self.connection.write(self.s)
                self.connection.flush()
                # transform photo stream to server
                self.connection.write(self.img_str)
                self.connection.flush()
        except Exception as e:
            print(e)
        finally:
            self.connection.close()

server_socket = socket.socket()
server_socket.bind(('127.0.0.1', 8002))

client_threads = []

while True:
    server_socket.listen(3)
    (conn, (ip, port)) = server_socket.accept()
    newthread = ClientThread(conn, ip, port)
    newthread.start()
    client_threads.append(newthread)





