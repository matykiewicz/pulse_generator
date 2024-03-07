import time
from typing import List

import pytest
from textual.pilot import Pilot

from pulse_generator.cli import main
from pulse_generator.engine import Engine


@pytest.mark.asyncio
async def test_main(command_line_args: List[str]) -> None:
    pilot: Pilot
    engine: Engine = main(blocking=False)
    async with engine.ui.run_test() as pilot:
        await pilot.press("5")
        time.sleep(1)
        await pilot.press("e")
        time.sleep(1)
        await pilot.press("a")
