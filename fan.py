import RPi.GPIO as GPIO
import time
import zmq
import threading

'''
Daemon process, for fan control
'''

def read_cpu_temp():
    temp = -1
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = f.readline()
    except Exception as e:
        print(f'Cannot read cpu temp!\n{e}')
    return float(temp)/1000



def get_fan():
    fan = {'pin_num': 14, 'pin' : None, 'is_active' : False}
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(14, GPIO.OUT)
    fan['pin'] = GPIO.PWM(14, 100)
    fan['pin'].start(0)
    return fan


def activate(fan):
    try:
        fan['pin'].ChangeDutyCycle(100)
    except Exception as e:
        print(f'[-] : {e}')
        return -1
    else:
        fan['is_active'] = True
        return 0

def stop(fan):
    try:
        fan['pin'].ChangeDutyCycle(0)
    except Exception as e:
        print(f'[-] : {e}')
        return -1
    else:
        fan['is_active'] = False
        return 0

_fan_running = True
def control_fan():
    fan = get_fan()
    stop(fan)
    threshold = 70
    time_threshold = 2
    t = time.time() - time_threshold
    try:
        while _fan_running:
            temp = read_cpu_temp()
            if not fan['is_active'] and temp >= threshold and time.time() - t > time_threshold:
                activate(fan)
                t = time.time()
            elif fan['is_active'] and temp <= threshold and time.time() - t > time_threshold:
                stop(fan)
                t = time.time()
            time.sleep(0.2)
        stop(fan)
    except BaseException as e:
        print('Exception occured! cleaning up!')
    finally:
        stop(fan)
        #fan['pin'].stop()
        #GPIO.cleanup()

thread = threading.Thread(target=control_fan)
thread.start()
context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:55556")
while True:
    message = socket.recv_string()
    print(message)
    if message == 'STOP':
        if _fan_running:
            _fan_running = False
            thread.join()
    elif message == 'START':
        if _fan_running:
            _fan_running = False
            thread.join()
        _fan_running = True
        thread = threading.Thread(target=control_fan)
        thread.start()
    elif message == 'QUIT':
        if _fan_running:
            _fan_running = False
            thread.join()
        socket.send_string('OK')
        socket.close()
        context.term()
        break

    socket.send_string('OK')



