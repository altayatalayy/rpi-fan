#!/bin/bash
cd /dev
chmod og+rwx gpio*
cd /home/ubuntu/fan
source venv/bin/activate
logfile=fan.log
python fan.py 1>>fan.log 2>>fan_e.log

