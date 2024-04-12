﻿# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.

# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Unit tests fixtures."""

from pathlib import Path
from shutil import rmtree

import pytest

from ansys.scade.apitools import scade


def pytest_configure(config):
    """Declare the markers used in this project."""
    config.addinivalue_line('markers', 'project: project to be loaded')


@pytest.fixture(scope='session')
def tmpdir():
    """Create/empty the temporary directory for output files."""
    path = (Path('tests') / 'tmp').resolve()
    try:
        rmtree(str(path))
    except FileNotFoundError:
        pass
    path.mkdir()
    return path


# scope is 'function' to re-initialize the projects which are modified
@pytest.fixture(scope='function')
def lrb(request):
    """Load and return the local, remote and base projects of a directory."""
    dir = Path(request.param)
    names = 'Local.etp', 'Remote.etp', 'Base.etp'
    return [scade.load_project(str(dir / _)) for _ in names]
