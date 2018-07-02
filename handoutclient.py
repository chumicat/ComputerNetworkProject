import socket
import struct
import PIL
from PIL import Image, ImageGrab
import numpy
import io
import logging
import socketserver
from threading import Condition, Thread
from http import server
import time
import datetime
import cv2
from fps import fps, ffps
from pynput.keyboard import Key, Listener

client_socket = socket.socket()
client_socket.connect(('127.0.0.1', 8002))
framesize = (320, 240)
connection = client_socket.makefile('wrb')
filename = ''
fromcamera = True
filflag = ''
frame = numpy.array([])
black = [0, 0, 0]
blackimg = numpy.array([ [black for i in range(framesize[0])] for i in range(framesize[1])])

'''
def on_press(key):
    print('{0} pressed'.format(
        key))
    print('{0}'.format(key))
    if '{0}'.format(key) == "u's'":
        print 'save'
        img = Image.fromarray(frame)
        img.save('temp.jpg')

def on_release(key):
    print('{0} release'.format(
        key))
    if key == Key.esc:
        # Stop listener
        return False

class KeyThread(Thread):
    def __init__(self):
        Thread.__init__(self)
    def run(self):
        # Collect events until released
        with Listener(
        on_press=on_press,
        on_release=on_release) as listener:
            listener.join()
'''

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
                    if isblack:
                        global frame
                        frame = blackimg
                    elif fromcamera:
                        global frame
                        ret, frame = self.cap.read()
                        frame = cv2.resize(frame, framesize, interpolation = cv2.INTER_AREA)
                    else:
                        global frame
                        frame = ImageGrab.grab()
                        frame = numpy.array(frame.resize(framesize, Image.ANTIALIAS))
                    # cv2.imshow("capture", frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                    # convert to jpg photo
                    global frame
                    frame = cv2_filter(frame, filflag)
                    img_str = cv2.imencode('.jpg', frame)[1].tostring()
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
            global fromcamera, isblack
            fromcamera = False
            isblack = False
        elif path == '/black':
            global isblack
            isblack = True
        elif path != '/' and path != '/index.html':
            global filename, fromcamera, isblack
            filename = path.strip('/')
            fromcamera = True
            isblack = False
        elif path == '/index.html':
            global filename, fromcamera, isblack
            fromcamera = True
            filename = ""
            isblack = False



#end StreamingHandler

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


output = StreamingOutput()

try:
    address = ('127.0.0.1', 8000)
    server = StreamingServer(address, StreamingHandler)
    # keyctrl = KeyThread()
    # keyctrl.start()
    server.serve_forever()
except Exception as e:
    print(e)
