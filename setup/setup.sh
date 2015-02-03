#!/bin/bash

set -e -x

unset HISTFILE

export DEBIAN_FRONTEND=noninteractive

# packages

ubuntu=utopic

cat > /etc/apt/sources.list << EOF
deb http://mirror.aarnet.edu.au/ubuntu/ $ubuntu main universe
deb http://mirror.aarnet.edu.au/ubuntu/ $ubuntu-updates main universe

deb http://security.ubuntu.com/ubuntu $ubuntu-security main universe
EOF

apt-get update
apt-get -y dist-upgrade
apt-get -y install dkms build-essential

# parallel dkms builds

patch /usr/sbin/dkms parallel-dkms/dkms.patch

# zfs

apt-add-repository --yes ppa:zfs-native/stable

apt-get update
apt-get -y install ubuntu-zfs

# java

add-apt-repository --yes ppa:webupd8team/java

echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections

apt-get update
apt-get -y install oracle-java8-installer

# other requirements

apt-get -y install `cat packages.txt`

pip install --upgrade python-novaclient python-keystoneclient python-glanceclient python-swiftclient django-storages

# patch django-storages

patch /usr/local/lib/python2.7/dist-packages/storages/backends/s3boto.py < s3boto.patch

# cleanup

apt-get clean

# zfs: boot-time initialisation

install -o 0 -g 0 rc.local /etc

# clear out keys and other things, ready for a snapshot

rm -vf /etc/ssh/ssh*key* /{root,home/ubuntu}/.ssh/authorized_keys /home/ubuntu/.cache/motd.legal-displayed

truncate -s 0 /var/log/wtmp /var/log/lastlog
