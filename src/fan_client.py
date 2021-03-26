import zmq
import argparse
import logging
import sys

logging.basicConfig(format='%(asctime)s:%(levelname)s:%(module)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG, filename='logs/fan.log')

cmds = ['STOP', 'START', 'QUIT']
parser = argparse.ArgumentParser(description='Fan controller client.')
parser.add_argument('cmd', type=str, help=f'{"|".join(cmds)}')
args = parser.parse_args()
cmd = args.cmd
if not cmd in cmds:
    logging.warn(f'Wrong command! got {cmd}, requires: {"|".join(cmds)}')
    sys.exit(-1)

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:55556")
logging.info('Connected to server')

def send_cmd(cmd):
    socket.send_string(cmd)
    resp = socket.recv_string()
    if resp != 'OK':
        logging.debug(f'Sent command : {cmd}, {resp}')

send_cmd(cmd)
socket.close()
context.term()
