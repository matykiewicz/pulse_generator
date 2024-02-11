#!/usr/bin/env python3
"""Play a sine signal."""
import argparse
import sys

import numpy as np
from scipy import signal
import sounddevice as sd


def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument(
    '-l', '--list-devices', action='store_true',
    help='show list of audio devices and exit')
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    'frequency', nargs='?', metavar='FREQUENCY', type=float, default=0.01,
    help='frequency in Hz (default: %(default)s)')
parser.add_argument(
    '-d', '--device', type=int_or_str,
    help='output device (numeric ID or substring)')
parser.add_argument(
    '-a', '--amplitude', type=float, default=300.0,
    help='amplitude (default: %(default)s)')
parser.add_argument(
    '-b', '--bpm', type=int, default=60,
    help='amplitude (default: %(default)s)')
parser.add_argument(
    '-s', '--size', type=int, default=10,
    help='amplitude (default: %(default)s)')
args = parser.parse_args(remaining)

try:

    sample_rate = sd.query_devices(args.device, 'output')['default_samplerate']
    block_size = 60 * int(sample_rate)
    pulses = np.zeros((block_size, 1))
    pulse = int(sample_rate * args.size / 1000)
    interval = (block_size // args.bpm) + 1
    for i in range(args.bpm):
        start = i * interval
        end = i * interval + pulse
        t = np.linspace(0, 0.5, pulse, endpoint=False)
        pulses[start : end, 0] = args.amplitude * signal.square(2 * np.pi * args.frequency * t)


    def callback(outdata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        outdata[:] = pulses

    with sd.OutputStream(device=args.device, channels=1, callback=callback,
                         samplerate=sample_rate, blocksize=60*int(sample_rate)):
        print('#' * 80)
        print('press Return to quit')
        print('#' * 80)
        input()
except KeyboardInterrupt:
    parser.exit('')
except Exception as e:
    parser.exit(type(e).__name__ + ': ' + str(e))

