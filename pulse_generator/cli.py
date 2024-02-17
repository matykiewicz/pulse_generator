import argparse
from argparse import Namespace

from .engine import Engine


def run(args: Namespace):
    Engine.start(args=args)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--frequency",
        type=float,
        default=0.01,
        help="frequency in Hz (default: %(default)s)",
    )
    parser.add_argument(
        "-a",
        "--amplitude",
        type=float,
        default=300.0,
        help="amplitude (default: %(default)s)",
    )
    parser.add_argument(
        "-b",
        "--bpm-init",
        type=int,
        default=60,
        help="initial beats per minute (default: %(default)s)",
    )
    parser.add_argument(
        "-l",
        "--length-pulse",
        type=int,
        default=10,
        help="pulse length (default: %(default)s)",
    )
    args = parser.parse_args()
    run(args=args)
