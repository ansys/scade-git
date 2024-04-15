# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

import json
from pathlib import Path
from typing import Any, List

import pytest
import scade.model.project.stdproject as std

from ansys.scade.apitools import scade
from ansys.scade.git.extension.gitclient import GitStatus
import ansys.scade.git.extension.gitextcore as core
from ansys.scade.git.extension.ide import Ide
from test_utils import cmp_file, get_resources_dir as get_tests_dir, run_git

# local constants for conciseness
ADDED = GitStatus.added
REMOVED_STAGED = GitStatus.removed_staged
MODIFIED_STAGED = GitStatus.modified_staged
REMOVED_UNSTAGED = GitStatus.removed_unstaged
MODIFIED_UNSTAGED = GitStatus.modified_unstaged
UNTRACKED = GitStatus.untracked
CLEAN = GitStatus.clean
EXTERN = GitStatus.extern


def get_resources_dir() -> Path:
    """Return the resources directory for these tests."""
    return get_tests_dir() / 'extension' / 'resources'


def get_ref_dir() -> Path:
    """Return the reference directory for these tests."""
    return get_tests_dir() / 'extension' / 'ref'


"""
    CmdCommit,
    CmdDiff as CoreCmdDiff,
    CmdRefresh,
    CmdReset,
    CmdResetAll as CoreCmdResetAll,
    CmdStage,
    CmdStageAll,
    CmdUnstage,
    CmdUnstageAll,
"""

class TestIde(Ide):
    """SCADE IDE instantiation for unit tests."""
    def __init__(self):
        self.project = None
        self.selection = []
        self.browser = None
        self.browser_items = None

    def create_browser(self, name: str, icon: str = ''):
        """Stub scade.create_browser."""
        self.browser = {'name': name, 'icon': Path(icon).name if icon else '', 'children': []}
        self.browser_items = {None: self.browser}

    def browser_report(
            self,
            item: Any,
            parent: Any = None,
            expanded: bool = False,
            name: str = '',
            icon_file: str = '',
        ):
        """Stub scade.browser_report."""
        if isinstance(item, str):
            child = item
        else:
            assert isinstance(item, std.Project) or isinstance(item, std.FileRef)
            child = '<%s> %s' % (type(item).__name__, name if name else item.pathname)
        parent = self.browser_items[parent]
        entry = {
            'name': child,
            'icon': Path(icon_file).name if icon_file else '',
            'expanded': expanded,
            'children': []
        }
        parent['children'].append(entry)
        self.browser_items[child] = entry

    def selection(self) -> List[Any]:
        """Stub scade.selection."""
        return self.selection

    def get_active_project(self) -> std.Project:
        """Stub scade.active_project."""
        return self.project

    def get_projects(self) -> List[Any]:
        """Stub scade.model.project.stdproject.get_roots."""
        return [self.get_active_project()]

    def log(self, text: str):
        """Stub scade.tabput."""
        print(text)

    def save_browser(self, path: Path):
        """Store the current browser as a json file."""
        with path.open('w') as f:
            json.dump(self.browser, f, indent='   ', sort_keys=True)


_test_ide = TestIde()

@pytest.fixture(scope='function')
def model_repo(request, git_repo):
    """
    Initializes a GitClient for Model/Model.etp.

    Get a temporary Git project from the resource directory
    and perform a few Git commands to make the repo consistent
    with the project's expected status.
    """
    tmp_dir = git_repo
    model_dir = tmp_dir /'Model'
    path = model_dir / 'untracked_file.txt'
    path.open('w').write('some content\n')
    path = model_dir / 'new.txt'
    path.open('w').write('new content\n')
    run_git('add', str(path), dir=tmp_dir)
    path = model_dir / 'modified_unstaged.txt'
    path.open('w').write('new content\n')
    path = model_dir / 'modified_staged.txt'
    path.open('w').write('new content\n')
    run_git('add', str(path), dir=tmp_dir)
    path = model_dir / 'removed_unstaged.txt'
    path.unlink()
    path = model_dir / 'removed_staged.txt'
    path.unlink()
    run_git('add', str(path), dir=tmp_dir)

    core.set_git_client(request.cls.git_client)

    return tmp_dir


@pytest.mark.repo(get_resources_dir())
@pytest.mark.usefixtures('model_repo')
class TestGitExtCoreBrowser:
    def test_cmd_refresh(self, capsys, tmpdir):
        project_path = self.dir / 'Model' / 'Model.etp'
        print('project path', project_path)
        _test_ide.project = scade.load_project(str(project_path))
        cmd = core.CmdRefresh(_test_ide)
        assert cmd.on_enable()
        cmd.on_activate()
        result = tmpdir / 'refresh.json'
        _test_ide.save_browser(result)
        ref = get_ref_dir() / 'refresh.json'

        # read the outputs issued before the diff
        captured = capsys.readouterr()
        # ignore the version number
        diff = cmp_file(ref, result, n = 0)
        for line in list(diff):
            print(line, end = '')
        #stdout.writelines(diff)
        captured = capsys.readouterr()
        assert captured.out == ''
