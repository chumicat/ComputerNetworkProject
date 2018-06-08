import io
import socket
import struct
import time
import datetime
import cv2

client_socket = socket.socket()
client_socket.connect(('127.0.0.1', 8002))

connection = client_socket.makefile('wb')
try:
    # open camera 
    cap = cv2.VideoCapture(0)
    while (1):
        # read photo
        ret, frame = cap.read()
        # cv2.imshow("capture", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
        # convert to jpg photo
        img_str = cv2.imencode('.jpg', frame)[1].tostring()
        
        # fetch length of photo
        s = struct.pack('<L', len(img_str))
        # print(s)
        
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
    client_socket.close()
