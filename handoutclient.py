import socket
import struct
import PIL
from PIL import Image, ImageGrab
import numpy
import io
import logging
import socketserver
from threading import Condition
from http import server
import time
import datetime
import cv2
from fps import fps, ffps

client_socket = socket.socket()
client_socket.connect(('127.0.0.1', 8002))
framesize = (320, 240)
connection = client_socket.makefile('wrb')
filename = ''
fromcamera = True
filflag = ''

def writehtml(size):
    x = size[0]
    y = size[1]
    img = '<img src="stream.mjpg" width="' + str(x * 4) + '" height="' + str(y * 2) \
     + '" />'
    return '''
    <html>
    <head>
    <title>camera MJPEG streaming demo</title>
    </head>
    <body>
    <h1>PiCamera MJPEG Streaming Demo</h1>''' + img + '''
    </body>
    </html>
    '''

PAGE = writehtml(framesize)

def cv2_filter(img, flag):
    if flag == 'None':
        return img
    elif flag == 'Pencil':
        dst1_gray, dst1_color = cv2.pencilSketch(img, sigma_s = 50, sigma_r = 0.15, shade_factor = 0.04)
        return dst1_color
    elif flag == 'Style':
        dst2 = cv2.stylization(img, sigma_s = 50, sigma_r = 0.15)
        return dst2
    elif flag == 'Detail':
        dst3 = cv2.detailEnhance(img, sigma_s = 50, sigma_r = 0.15)
        return dst3
    elif flag == 'Edge':
        dst4 = cv2.edgePreservingFilter(img, flags=1, sigma_s = 50, sigma_r = 0.15)
        return dst4
    elif flag == 'udinverse':
        return img[::-1]
    elif flag == 'lrinverse':
        return cv2.flip(img, flipCode = 1)
        # return LRinv(img)

class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


class StreamingHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        elif self.path == '/index.html':
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        elif self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                # open camera 
                if fromcamera:
                    if len(filename) > 0:
                        self.cap = cv2.VideoCapture(filename)
                    else:
                        self.cap = cv2.VideoCapture(0)
                while True:
                    print(ffps())
                    #client send image
                    # read photo
                    if fromcamera:
                        ret, self.frame = self.cap.read()
                        self.frame = cv2.resize(self.frame, framesize, interpolation = cv2.INTER_AREA)
                    else:
                        self.frame = ImageGrab.grab()
                        self.frame = numpy.array(self.frame.resize(framesize, Image.ANTIALIAS))
                    # cv2.imshow("capture", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    # convert to jpg photo
                    self.frame = cv2_filter(self.frame, filflag)
                    img_str = cv2.imencode('.jpg', self.frame)[1].tostring()
                    # fetch length of photo
                    s = struct.pack('<L', len(img_str))
                    # transform length to server
                    connection.write(s)
                    connection.flush()
                    # transform photo stream to server
                    connection.write(img_str)
                    connection.flush()

                    #cleient get image
                    # fetch length of photo
                    image_len = struct.unpack('<L', connection.read(struct.calcsize('<L')))[0]
                    if not image_len:
                        break

                    image_stream = io.BytesIO()
                    # read photo
                    image_stream.write(connection.read(image_len))

                    image_stream.seek(0)
                    image = Image.open(image_stream)
                    cv2img = numpy.array(image, dtype=numpy.uint8)
                    imgbuffer = image_stream.getvalue()
                    # write to http response
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(imgbuffer))
                    self.end_headers()
                    self.wfile.write(imgbuffer)
                    self.wfile.write(b'\r\n')
            except:
                exit(1)
        elif self.path == '/favicon.ico':
            self.send_response(301)
            self.send_header('Location', '/index.html')
            self.end_headers()
        else:
            args = self.path.split('&')
            self.setframe(args[0])
            if len(args) > 1:
                global filflag
                filflag = args[1].split('=')[1]
            else:
                global filflag
                filflag = 'None'
            content = PAGE.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)

    def setframe(self, path):
        # /screenshot for screenshot
        # / or /index.html for camera
        # /... for readfile
        if path == '/screen.shot':
            global fromcamera
            fromcamera = False
        elif path != '/' and path != '/index.html':
            global filename, fromcamera
            filename = path.strip('/')
            fromcamera = True
        elif path == '/index.html':
            global filename, fromcamera
            fromcamera = True
            filename = ""


#end StreamingHandler

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


output = StreamingOutput()

try:
    address = ('127.0.0.1', 8000)
    server = StreamingServer(address, StreamingHandler)
    server.serve_forever()
except Exception as e:
    print(e)
