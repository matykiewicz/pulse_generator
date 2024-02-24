import sys
from typing import List

import pytest


@pytest.fixture
def command_line_args() -> List[str]:
    sys.argv = [__file__]
    return sys.argv
