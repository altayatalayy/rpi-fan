import RPi.GPIO as GPIO
import time
import zmq
import threading
import sys
import logging
import argparse


parser = argparse.ArgumentParser(description='Fan controller server.')
parser.add_argument('--config', default=False, action='store_true')
parser.add_argument('--pin', type=int, required='--config' in sys.argv)
args = parser.parse_args()

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG, filename='logs/fan.log')

class Fan:

    def __init__(self, pin_num=14):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_num, GPIO.OUT)
        self.pin = GPIO.PWM(pin_num, 100)
        self.pin.start(0)
        self.pin_num = pin_num
        self.is_active = False

    @staticmethod
    def from_file(filepath='config.json'):
        import json
        with open(filepath) as f:
            conf = json.load(f)
        return Fan(pin_num=conf['pin'])

    def save_file(self, filepath='config.json'):
        import json
        d = {'pin' : fan.pin_num}
        with open(filepath, 'w') as f:
            json.dump(d, f)

    def start(self):
        self.pin.ChangeDutyCycle(100)
        self.is_active = True

    def stop(self):
        self.pin.ChangeDutyCycle(0)
        self.is_active = False

if args.config:
    fan = Fan(pin_num=args.pin)
    fan.save_file()
    sys.exit(0)


def read_cpu_temp():
    temp = None
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = f.readline()
    except Exception as e:
        logging.error((f'Cannot read cpu temp!\n{e}'))
    return float(temp)/1000


_fan_running = True
def control_fan():
    fan = Fan.from_file()
    fan.stop()
    threshold = 70
    time_threshold = 30
    t = time.time() - time_threshold
    try:
        while _fan_running:
            temp = read_cpu_temp()
            if not fan.is_active and temp >= threshold and time.time() - t > time_threshold:
                fan.start()
                t = time.time()
                logging.info(f'Activated Fan cpu temp = {temp:3.1f}')
            elif fan.is_active and temp <= threshold and time.time() - t > time_threshold:
                fan.stop()
                t = time.time()
                logging.info(f'Stopped Fan cpu temp = {temp:3.1f}')
            time.sleep(0.8)
        fan.stop()
    except BaseException as e:
        logging.debug('{e}')
    finally:
        fan.stop()
        #fan['pin'].stop()
        #GPIO.cleanup()

'''
Daemon process, for fan control
'''


thread = threading.Thread(target=control_fan)
thread.start()
logging.info('Started thread')

context = zmq.Context()
socket = context.socket(zmq.REP)
port = 55556
socket.bind(f"tcp://*:{port}")
logging.info(f'Server started listening on port : {port}')
while True:
    message = socket.recv_string()
    logging.debug(f'recived {message}')
    if message == 'STOP':
        if _fan_running:
            _fan_running = False
            thread.join()
        logging.debug('Stopped thread')

    elif message == 'START':
        if _fan_running:
            _fan_running = False
            thread.join()
        _fan_running = True
        thread = threading.Thread(target=control_fan)
        thread.start()
        logging.debug(f'Restarted thread')

    elif message == 'QUIT':
        if _fan_running:
            _fan_running = False
            thread.join()
        socket.send_string('OK')
        socket.close()
        context.term()
        logging.debug('Stopped thread and cleaned up')
        break

    socket.send_string('OK')


