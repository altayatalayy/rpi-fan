#!/bin/bash

cd /home/ubuntu/fan
source venv/bin/activate

python fan_client.py $1
