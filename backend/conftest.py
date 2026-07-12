"""Pytest bootstrap: put the backend root on sys.path so ``import app.*`` works
when tests are run with ``pytest`` from the ``backend/`` directory.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
