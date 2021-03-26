#!/bin/bash
cd /home/ubuntu/fan/

builddir=fan_0.1.0
if [[ ! -d "$builddir" ]]; then
	mkdir -p $builddir/DEBIAN
	echo "created $builddir"
	echo "#!/bin/bash" > $builddir/DEBIAN/postinst
	echo "sudo systemctl daemon-reload" >> $builddir/DEBIAN/postinst
	sudo chmod 0775 $builddir/DEBIAN/postinst
	touch $builddir/DEBIAN/control
	echo "creted DEBIAN/control please fill in the file"
	exit 0
fi

mkdir -p $builddir/usr/bin
mkdir -p $builddir/etc/fan
mkdir -p $builddir/etc/systemd/system
cp fan/bin/fan.py $builddir/usr/bin/fan
cp fan/config.json $builddir/etc/fan/
cp fan/fan.service $builddir/etc/systemd/system

dpkg-deb --build fan_0.1.0/
