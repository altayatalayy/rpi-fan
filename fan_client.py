import zmq
import argparse

cmds = ['STOP', 'START', 'QUIT']
parser = argparse.ArgumentParser(description='Fan controller client.')
parser.add_argument('cmd', type=str, help=f'{"|".join(cmds)}')
args = parser.parse_args()
cmd = args.cmd
if not cmd in cmds:
    print(f'Wrong command! got {cmd}, requires: {"|".join(cmds)}')

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:55556")

def send_cmd(cmd):
    socket.send_string(cmd)
    resp = socket.recv_string()
    if resp != 'OK':
        print('failed! resp={resp}')

send_cmd(cmd)
socket.close()
context.term()
