import socket
import numpy as np
import cv2
from PIL import Image

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
HOST, PORT = '127.0.0.1', 80
s.bind((HOST, PORT))
cap = cv2.VideoCapture(0)
Here = '127.0.0.1'

def error404(tcpClient):
    tcpClient.send('HTTP/1.0 404 Not Found\r\n')
    tcpClient.send('Content-Type:text/html; charset = utf-8\r\n')
    tcpClient.send('Connection: close\r\n')
    tcpClient.send('Content-Length: 15\r\n')
    tcpClient.send('\r\n') #end of header
    tcpClient.send('404 Not Found\r\n')

def writeHTML(ipaddr):
    f = open('test.html', 'w')
    f.write('<html>')
    f.write('<head>')
    f.write('</head>')
    f.write('<body>')
    f.write('<p> <img src = ' + ipaddr + '/sample.jpeg' + '> </p>')
    f.write('</body>')

a = 0
file = ""
while True:
    s.listen(0)
    tcpClient, address = s.accept()
    message = tcpClient.recv(1000)
    # print message
    if len(message) == 0:
        error404(tcpClient)
    x = message.split()
    if len(x) > 1:
        file = x[1].strip('/')
        if x[len(x)-1].find('statement') >= 0:
            print x[len(x)-1].split('=')[1] #data is here
    else:
        print message
    try:
        f = open('test.html', 'r')
        data = f.read()
        contentLength = len(data)
        tcpClient.send('HTTP/1.0 200 OK\r\n')
        tcpClient.send('Content-Type:text/html; charset = utf-8\r\n')
        tcpClient.send('Connection: close\r\n')
        tcpClient.send('\r\n') #end of header
        tcpClient.send(data)
    except:
        print 'Did not find the file'
        error404(tcpClient)
