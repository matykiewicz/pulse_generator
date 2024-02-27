#
# dtoverlay=vc4-fkms-v3d
#
# sudo apt-get install libportaudio2 libasound-dev
# sudo apt-get install python3-pip python3-venv
# sudo apt-get install alsa alsa-utils
# sudo apt install python3.9 python3.9-venv
# python3 -m venv ~/.venv
# ~/.venv/bin/pip3 install poetry
sudo setfont /usr/share/consolefonts/Lat7-Terminus32x16.psf.gz
amixer -c 0 sset 'PCM' 85%
amixer -c 1 sset 'PCM' 85%
amixer -c 2 sset 'PCM' 85%
amixer -c 3 sset 'PCM' 85%
amixer -c 4 sset 'PCM' 85%
source ~/.venv/bin/activate
cd ~/pulse_generator/
rm -rf rm poetry.lock
~/.venv/bin/poetry install
~/.venv/bin/poetry run python3 ./pulse_generator/cli.py -t 120 -s 16 -w 1 -a 1 -f 50
