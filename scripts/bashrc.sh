
amixer -c 0 sset 'PCM' 100%
amixer -c 1 sset 'PCM' 100%
amixer -c 2 sset 'PCM' 100%
amixer -c 3 sset 'PCM' 100%
amixer -c 4 sset 'PCM' 100%
source ~/.venv/bin/activate
cd ~/pulse_generator/
../.venv/bin/poetry run python3 ./pulse_generator/cli.py -t 120 -s 16 -w 1

