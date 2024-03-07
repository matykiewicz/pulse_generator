import argparse
from argparse import Namespace

from pulse_generator.engine import Engine


def run(args: Namespace, blocking: bool) -> Engine:
    return Engine.run(args=args, blocking=blocking)


def main(blocking: bool) -> Engine:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--frequency",
        type=float,
        default=400,
        help="frequency in Hz (default: %(default)s)",
    )
    parser.add_argument(
        "-a",
        "--amplitude",
        type=float,
        default=1.0,
        help="amplitude (default: %(default)s)",
    )
    parser.add_argument(
        "-t",
        "--tempos-init",
        type=int,
        default=60,
        help="initial beats per minute (default: %(default)s)",
    )
    parser.add_argument(
        "-s",
        "--steps-init",
        type=int,
        default=4,
        help="initial steps per part (default: %(default)s)",
    )
    parser.add_argument(
        "-w",
        "--waits-init",
        type=int,
        default=1,
        help="initial no. of parts to wait when paused (default: %(default)s)",
    )
    parser.add_argument(
        "-r",
        "--rands-init",
        type=int,
        default=1,
        help="initial no. of parts to wait when paused (default: %(default)s)",
    )
    parser.add_argument(
        "-m",
        "--rands-magnitude",
        type=float,
        default=0.5,
        help="strength of the pulse randomness between 0 and 1 (default: %(default)s)",
    )
    parser.add_argument(
        "-d",
        "--device-match",
        type=str,
        default="USB Audio",
        help="initial beats per minute (default: %(default)s)",
    )
    args = parser.parse_args()
    return run(args=args, blocking=blocking)


if __name__ == "__main__":
    main(blocking=True)
