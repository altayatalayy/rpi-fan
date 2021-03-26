#!/bin/bash
cd /home/ubuntu/fan
FILE=config.json
if [[ ! -f "$FILE" ]]; then
	echo -n "Enter pin num: "
	read n
	source venv/bin/activate
	python src/fan.py --config --pin $n
fi

cp /home/ubuntu/fan/scripts/fan.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fan.service
