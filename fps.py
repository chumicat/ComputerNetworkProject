from datetime import datetime

fps_t_last = datetime.now()
fps_s_last = 0

def ffps():
    # declare global variable
    global fps_t_last
    global fps_s_last
    
    # Calculate FPS
    fps_t_now = datetime.now()
    delta_t = fps_t_now - fps_t_last # delta in time mode
    delta_s = delta_t.seconds + delta_t.microseconds/1E6 # delta in second
    fps_s_last = fps_s_last*0.8 + (1/delta_s)*0.2 # simple fluence the fps
    #print(int(fps_s_last))
    fps_t_last = fps_t_now # record data
    
    return int(fps_s_last)

def fps():
    # declare global variable
    global fps_t_last
    
    # Calculate FPS
    fps_t_now = datetime.now()
    delta_t = fps_t_now - fps_t_last # delta in time mode
    delta_s = delta_t.seconds + delta_t.microseconds/1E6 # delta in second
    fps_t_last = fps_t_now # record data
    
    return int(1/delta_s)