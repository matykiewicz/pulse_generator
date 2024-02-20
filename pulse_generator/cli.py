import argparse
from argparse import Namespace

from pulse_generator.engine import Engine


def run(args: Namespace) -> Engine:
    return Engine.start(args=args)


def main() -> Engine:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-f",
        "--frequency",
        type=float,
        default=10,
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
        "-d",
        "--device-match",
        type=str,
        default="USB Audio",
        help="initial beats per minute (default: %(default)s)",
    )
    args = parser.parse_args()
    return run(args=args)


if __name__ == "__main__":
    main()
