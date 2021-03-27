#!/bin/python3
import RPi.GPIO as GPIO
import time
import zmq
import threading
import sys
import logging
import argparse


cmds = ['STOP', 'START', 'QUIT', 'STATUS']
parser = argparse.ArgumentParser(description='Fan controller python script.')
parser.add_argument('--cmd', type=str, default='STATUS', help=f'{"|".join(cmds)}', required=False)
parser.add_argument('--create-server', default=False, action='store_true')
parser.add_argument('--config', default=False, action='store_true')
parser.add_argument('--pin', type=int, required='--config' in sys.argv)
args = parser.parse_args()

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG, filename='/var/log/fan.log')

class Fan:

    def __init__(self, pin_num=14):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin_num, GPIO.OUT)
        self.pin = GPIO.PWM(pin_num, 100)
        self.pin.start(0)
        self.pin_num = pin_num
        self.is_active = False

    @staticmethod
    def from_file(filepath='/etc/fan/config.json'):
        import json
        with open(filepath) as f:
            conf = json.load(f)
        return Fan(pin_num=conf['pin'])

    def save_file(self, filepath='/etc/fan/config.json'):
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


def read_cpu_temp():
    temp = None
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = f.readline()
    except Exception as e:
        logging.error((f'Cannot read cpu temp!\n{e}'))
    return float(temp)/1000


_fan_running = True
fan = None
def control_fan():
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
            time.sleep(1.5)
        fan.stop()
    except BaseException as e:
        logging.debug('{e}')
    finally:
        fan.stop()
        #fan['pin'].stop()
        #GPIO.cleanup()

if args.config:
    fan = Fan(pin_num=args.pin)
    fan.save_file()
    sys.exit(0)


if args.create_server:
    '''
    Daemon process, for fan control
    '''
    fan = Fan.from_file()


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

        elif message == 'STATUS':
            resp = f'{read_cpu_temp():5.2f};{fan.is_active}'
            socket.send_string(resp)
            continue

        socket.send_string('OK')
    socket.close()
    context.term()
    sys.exit(0)



cmd = args.cmd
if not cmd in cmds:
    logging.warn(f'Wrong command! got {cmd}, requires: {"|".join(cmds)}')
    sys.exit(-1)

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:55556")
socket.RCVTIMEO = 1500
logging.info('Connected to server')

def send_cmd(cmd):
    socket.send_string(cmd)
    resp = socket.recv_string()
    if cmd == 'STATUS':
        return resp.split(';')
    if resp != 'OK':
        logging.debug(f'Sent command : {cmd}, {resp}')

if cmd == 'STATUS':
    while True:
        try:
            resp = send_cmd(cmd)
            msg = f''' STATUS:
    CPU TEMP : {resp[0]}
    FAN ACTIVE : {resp[1]}
'''
            sys.stdout.write(msg)
            sys.stdout.flush()
            time.sleep(0.15)
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[F")
            sys.stdout.write("\r")
            sys.stdout.flush()
        except Exception as e:
            logging.debug('Server not responding!')
            sys.exit(0)
        except BaseException as e:
            logging.debug(f'Exception {e}')
            break
else:
    try:
        send_cmd(cmd)
    except Exception as e:
        logging.debug('Server not responding!\n{e}')
        print('Server not responding')
        sys.exit(0)

socket.close()
context.term()

