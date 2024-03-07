#! /bin/bash

amixer -c 0 sset 'PCM' 85%
amixer -c 1 sset 'PCM' 85%
amixer -c 2 sset 'PCM' 85%
amixer -c 3 sset 'PCM' 85%
amixer -c 4 sset 'PCM' 85%
amixer -c 5 sset 'PCM' 85%
amixer -c 6 sset 'PCM' 85%
sleep 1
source ~/.venv/bin/activate
cd ~/pulse_generator/
rm -rf rm poetry.lock
~/.venv/bin/poetry install
~/.venv/bin/poetry run python3 ./pulse_generator/cli.py -t 120 -s 16 -w 1 -a 2 -r 1 -m 0.50 -f 60

