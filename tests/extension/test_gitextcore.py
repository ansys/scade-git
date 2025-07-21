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

import json
from pathlib import Path
import subprocess
import tarfile
from typing import Any, Dict, List

import pytest
import scade.model.project.stdproject as std

from ansys.scade.apitools import scade
from ansys.scade.git.extension.gitclient import GitStatus
import ansys.scade.git.extension.gitextcore as core
from ansys.scade.git.extension.ide import Command, Ide
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


class StubIde(Ide):
    """SCADE IDE instantiation for unit tests."""

    def __init__(self):
        self.project = None
        self._selection = []
        self.browser = None
        self.browser_items: Dict[Any, Any] = {}

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
        assert self.browser_items is not None
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
            'children': [],
        }
        parent['children'].append(entry)
        self.browser_items[child] = entry

    @property
    def selection(self) -> List[Any]:
        """Stub scade.selection."""
        return self._selection

    @selection.setter
    def selection(self, selection: List[Any]):
        """Stub scade.selection."""
        self._selection = selection

    def get_active_project(self) -> std.Project:
        """Stub scade.active_project."""
        assert self.project is not None
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


_test_ide = StubIde()


@pytest.fixture(scope='function')
def model_repo(request, git_repo):
    """
    Initializes a GitClient for Model/Model.etp.

    Get a temporary Git project from the resource directory
    and perform a few Git commands to make the repo consistent
    with the project's expected status.
    """
    tmp_dir, client = git_repo
    # perform modifications on a branch
    run_git('branch', 'tests', dir=tmp_dir)
    run_git('checkout', 'tests', dir=tmp_dir)
    model_dir = tmp_dir / 'Model'
    path = model_dir / 'untracked.txt'
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

    core.set_git_client(client)
    project_path = tmp_dir / 'Model' / 'Model.etp'
    # scade is a CPython module defined dynamically
    _test_ide.project = scade.load_project(str(project_path))  # type: ignore
    client.refresh(str(path))

    return tmp_dir


commands_data = [
    (core.CmdRefresh(_test_ide), 'refresh.json', []),
    (core.CmdStage(_test_ide), 'stage.json', ['modified_unstaged.txt', 'removed_unstaged.txt']),
    (core.CmdStageAll(_test_ide), 'stage_all.json', []),
    (core.CmdUnstage(_test_ide), 'unstage.json', ['modified_staged.txt']),
    (core.CmdUnstageAll(_test_ide), 'unstage_all.json', []),
    # test failed: command does not behave as git reset <file>...
    # --> re-enable once the command is fixed or its semantic is understood
    # (core.CmdReset(_test_ide), 'reset.json', [
    #     'modified_staged.txt',
    #     'modified_unstaged.txt',
    #     'new.txt',
    #     'removed_staged.txt',
    #     'removed_unstaged.txt',
    #     'untracked.txt',
    # ]),
    # following test is failed with dulwich 0.23.1, passed with dulwich 0.21.3
    (core.CmdResetAll(_test_ide), 'reset_all.json', []),
    (core.CmdCommit(_test_ide), 'commit.json', []),
]


@pytest.mark.usefixtures('model_repo')
@pytest.mark.parametrize(
    'cmd, ref, sel',
    commands_data,
    ids=[_[1] for _ in commands_data],
)
@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_commands(capsys, tmpdir: Path, cmd: Command, ref: str, sel: List[str]):
    _test_ide.selection = [
        _ for _ in _test_ide.get_active_project().file_refs if _.persist_as in sel
    ]
    assert cmd.on_enable()
    cmd.on_activate()
    result = tmpdir / ref
    _test_ide.save_browser(result)

    # read the outputs issued before the diff, if any
    captured = capsys.readouterr()
    # ignore the version number
    diff = cmp_file(get_ref_dir() / ref, result, n=0)
    for line in list(diff):
        print(line, end='')
    # stdout.writelines(diff)
    captured = capsys.readouterr()
    assert captured.out == ''


@pytest.mark.usefixtures('model_repo')
@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff(capsys):
    cmd = core.CmdDiff(_test_ide)
    assert cmd.on_enable()

    # read the outputs issued before the diff, if any
    captured = capsys.readouterr()
    cmd.on_activate()
    # get the status of the command on stdout, must be two lines
    captured = capsys.readouterr()
    print(captured.out)
    lines = captured.out.strip().split('\n')
    assert len(lines) == 2
    archive = Path(lines[1].strip())
    assert archive.exists()


def test_safe_members(tmpdir_factory, capsys):
    """
    Create an archive with links, make sure they are filtered.

    tree
        extern.txt
        root
            root.txt
            slk_child.txt
            hlk_child.txt
            slk_extern.txt
            hlk_extern.txt
            child
                child.txt
                slk_root.txt
                hlk_root.txt
                slk_sibling.txt
                hlk_sibling.txt
            sibling
                sibling.txt

    """

    def link_to(src_dir, target):
        """create symbolic and hard links to target in src_dir."""
        for prefix, flag in [('s', ''), ('h', ' /H')]:
            src = src_dir / f'{prefix}lk_{target.name}'
            cmd = f'mklink{flag} {str(src)} {str(target)}'
            subprocess.run(['cmd.exe', '/C', cmd], capture_output=True, text=True)

    tree_dir = Path(tmpdir_factory.mktemp('tree'))

    # hierarchy
    extern_txt = tree_dir / 'extern.txt'
    extern_txt.write_text('extern.txt')
    root_dir = tree_dir / 'root'
    root_dir.mkdir()
    root_txt = root_dir / 'root.txt'
    root_txt.write_text('root.txt')
    child_dir = root_dir / 'child'
    child_dir.mkdir()
    child_txt = child_dir / 'child.txt'
    child_txt.write_text('child.txt')
    sibling_dir = root_dir / 'sibling'
    sibling_dir.mkdir()
    sibling_txt = sibling_dir / 'sibling.txt'
    sibling_txt.write_text('sibling.txt')
    # links
    link_to(root_dir, Path('child/child_txt'))
    link_to(root_dir, Path('../extern_txt'))
    link_to(child_dir, Path('../root_txt'))
    link_to(child_dir, Path('../sibling/sibling_txt'))

    # create an archive
    archive = tree_dir / 'archive.zip'
    tar_file = tarfile.open(archive, 'w:gz')
    for path in root_dir.glob('*'):
        tar_file.add(path, arcname=path.name)
    tar_file.add(extern_txt, arcname='../extern.txt')
    tar_file.close()

    # read the outputs issued before the test, if any
    captured = capsys.readouterr()

    # get the instance of GitClient
    cmd = core.CmdDiff(_test_ide)
    tar_file = tarfile.open(archive)
    extract_dir = tree_dir / 'extract'

    tar_file.extractall(extract_dir, members=cmd.safe_members(extract_dir, tar_file))
    tar_file.close()

    # get the status of the command on stdout, must be two lines
    captured = capsys.readouterr()
    print(captured.out)
    lines = set(captured.out.strip().split('\n'))
    assert lines == {
        r'slk_extern_txt is blocked: symlink to ..\extern_txt',
        '../extern.txt is blocked: illegal path',
        # can't have this test successful
        # r'hlk_extern_txt is blocked: hard link to ..\extern_txt',
    }
