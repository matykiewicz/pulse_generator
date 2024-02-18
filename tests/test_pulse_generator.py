import time

from pulse_generator.cli import main
from pulse_generator.engine import Engine


def test_main(command_line_args):
    engine: Engine = main()
    time.sleep(1000)
    engine.finish()
