# Copyright (C) 2023 - 2025 ANSYS, Inc. and/or its affiliates.
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
from shutil import copytree, rmtree
from typing import Tuple

import pytest

from ansys.scade.apitools import scade
from ansys.scade.git.extension.gitclient import GitClient
from test_utils import run_git


def pytest_configure(config):
    """Declare the markers used in this project."""
    config.addinivalue_line('markers', 'repo: repository to duplicate')


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
    # scade is a CPython module defined dynamically
    return [scade.load_project(str(dir / _)) for _ in names]  # type: ignore


class TestGitClient(GitClient):
    def log(self, text):
        """Print the logs to the standard output."""
        print(text)


@pytest.fixture(scope='class')
def tmp_repo(request, tmpdir_factory) -> Tuple[Path, GitClient]:
    """
    Initializes a GitClient for a test directory which is not tracked.

    The client is initialized from a temporary copy of the input repo.
    """
    # behaves as a __init__ method for request.cls
    marker = request.node.get_closest_marker('repo')
    # marker is None if the test is not designed correctly
    assert marker
    path = marker.args[0]
    tmp_repos = Path(tmpdir_factory.mktemp('repos'))
    tmp_dir = tmp_repos / path.name
    copytree(path, tmp_dir)

    # get the instance of GitClient
    git_client = TestGitClient()
    status = git_client.get_init_status()
    assert status
    return tmp_dir, git_client


@pytest.fixture(scope='class')
def git_repo(request, tmp_repo) -> Tuple[Path, GitClient]:
    """
    Initializes a GitClient for a test repository.

    Create a Git repository from the temporary directory and add all files.
    """
    tmp_dir, client = tmp_repo
    # create git repo and add all files
    run_git('init', '-b', 'main', str(tmp_dir))
    # runt the next commands in the context of the git repo
    run_git('add', str(tmp_dir), dir=tmp_dir)
    run_git('commit', '-m', 'copy', dir=tmp_dir)

    return tmp_dir, client
