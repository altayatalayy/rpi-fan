#!/bin/bash
cp /home/ubuntu/fan/fan.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fan.service
