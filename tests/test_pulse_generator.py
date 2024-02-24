import time
from typing import List

from pulse_generator.cli import main
from pulse_generator.engine import Engine


def test_main(command_line_args: List[str]) -> None:
    engine: Engine = main(blocking=False)
    engine.ui.run()
    time.sleep(1000)
    engine.finish()
