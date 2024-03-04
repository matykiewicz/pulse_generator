#! /bin/bash

# OS level changes

sudo apt -y update
sudo apt -y upgrade
sudo apt -y install libportaudio2 libasound-dev
sudo apt -y install alsa alsa-utils
sudo apt -y install python3.9 python3.9-venv python3.9-dev
sudo systemctl set-default multi-user.target
sudo sed -i 's/#NAutoVTs/NAutoVTs/'  /etc/systemd/logind.conf
sudo sed -i 's/#ReserveVT/ReserveVT/'  /etc/systemd/logind.conf
sudo mkdir -p /etc/systemd/system/getty@tty1.service.d/
sudo cp ~/pulse_generator/scripts/override.conf /etc/systemd/system/getty@tty1.service.d/override.conf
sudo sed -i 's/8x16/10x20/' /etc/default/console-setup
sleep 1

# User level changes

sudo su jetson -c 'python3.9 -m venv ~/.venv'
sudo su jetson -c '~/.venv/bin/pip3 install poetry'
sudo su jetson -c 'echo "~/pulse_generator/scripts/bashrc.sh" >> ~/.bashrc'
sleep 1

# Make it work!

sudo reboot now

