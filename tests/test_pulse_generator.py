import time

from pulse_generator.cli import main
from pulse_generator.engine import Engine


def test_main(command_line_args):
    engine: Engine = main(blocking=False)
    engine.ui.run()
    time.sleep(200)
    engine.finish()
