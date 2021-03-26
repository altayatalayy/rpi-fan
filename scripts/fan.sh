#!/bin/bash
cd /dev
chmod og+rwx gpio*
cd /home/ubuntu/fan
source venv/bin/activate
python src/fan.py

