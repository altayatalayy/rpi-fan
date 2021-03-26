#!/bin/bash

cd /home/ubuntu/fan
source venv/bin/activate

python src/fan_client.py $1
