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

apt-add-repository --yes ppa:zfs-native/stable

apt-get update
apt-get -y dist-upgrade
apt-get -y install dkms build-essential ubuntu-zfs

# zfs: boot-time initialisation

install -o 0 -g 0 rc.local /etc

# clear out keys and other things, ready for a snapshot

rm -vf rc.local /etc/ssh/ssh*key* /{root,home/ubuntu}/.ssh/authorized_keys /home/ubuntu/.cache/motd.legal-displayed

truncate -s 0 /var/log/wtmp /var/log/lastlog

# bye

poweroff
