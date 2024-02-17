import sys

import pytest


@pytest.fixture
def command_line_args():
    sys.argv = [__file__]
