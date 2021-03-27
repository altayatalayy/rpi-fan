#!/bin/bash
cd /home/ubuntu/fan/

builddir=fan_0.1.0

if [[ -d "$builddir" ]]; then
	rm -rf $builddir
fi

if [[ -f "$builddir.deb" ]]; then
	sudo rm "$builddir.deb"
fi

mkdir $builddir/
echo "created $builddir"
mkdir $builddir/DEBIAN/

cp scripts/DEBIAN/control $builddir/DEBIAN/
cp scripts/DEBIAN/postinst $builddir/DEBIAN/
sudo chmod 0775 $builddir/DEBIAN/postinst

mkdir -p $builddir/usr/bin
mkdir -p $builddir/etc/fan
mkdir -p $builddir/etc/systemd/system
cp fan/bin/fan.py $builddir/usr/bin/fan
cp fan/config.json $builddir/etc/fan/
cp fan/fan.service $builddir/etc/systemd/system

dpkg-deb --build fan_0.1.0/
