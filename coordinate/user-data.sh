#!/bin/sh

wget -O - https://github.com/modc08/nectar-ubuntu-zfs-image/archive/master.tar.gz | tar xzvf -

( cd nectar-ubuntu-zfs-image-master/setup ; ./setup.sh )

rm -rf nectar-ubuntu-zfs-image-master

poweroff
