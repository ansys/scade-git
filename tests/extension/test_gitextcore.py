# Copyright (C) 2023 - 2026 ANSYS, Inc. and/or its affiliates.
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

import builtins
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, List
from unittest.mock import Mock
import warnings

import pytest
import scade.model.project.stdproject as std

from ansys.scade.apitools import scade
from ansys.scade.git.extension.gitclient import GitStatus
import ansys.scade.git.extension.gitextcore as core
from ansys.scade.guitools.command import Command
from ansys.scade.guitools.stubs import StubIde
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


class TestIde(StubIde):
    """SCADE IDE instantiation for unit tests."""

    __test__ = False

    def browser_report(
        self,
        child_object: Any,
        parent_object: Any = None,
        expanded: bool = False,
        user_data: Any = None,
        name: str = '',
        icon_file: str = '',
    ):
        """Stub scade.browser_report."""
        # redefine generic implementation to get more readable names
        if isinstance(child_object, str):
            child = child_object
        else:
            assert isinstance(child_object, std.Project) or isinstance(child_object, std.FileRef)
            child = '<%s> %s' % (
                type(child_object).__name__,
                name if name else child_object.pathname,
            )
        super().browser_report(child, parent_object, expanded, user_data, name, icon_file)


def get_resources_dir() -> Path:
    """Return the resources directory for these tests."""
    return get_tests_dir() / 'extension' / 'resources'


def get_ref_dir() -> Path:
    """Return the reference directory for these tests."""
    return get_tests_dir() / 'extension' / 'ref'


_test_ide = TestIde()


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


@pytest.fixture(scope='function')
def model_repo_with_submodule(model_repo):
    """
    Initializes a GitClient for Model/Model.etp with LibSubModule as a submodule.

    Use the same Model resource as ``model_repo``. Its LibSubModule directory is
    moved into a standalone repository, then re-added at the same path as a
    Git submodule.
    """
    from shutil import copytree

    tmp_dir = model_repo
    client = core._git_client
    assert client is not None
    model_dir = tmp_dir / 'Model'
    submodule_dir = model_dir / 'LibSubModule'
    submodule_repo_dir = tmp_dir.parent / 'LibSubModuleRepo'

    # Create a standalone repository from the existing model library.
    copytree(submodule_dir, submodule_repo_dir)
    run_git('init', '-b', 'main', str(submodule_repo_dir))
    run_git('add', '.', dir=submodule_repo_dir)
    assert run_git('commit', '-m', 'submodule initial commit', dir=submodule_repo_dir)

    # Replace the regular directory with a submodule at the same model path.
    assert run_git('rm', '-r', 'Model/LibSubModule', dir=tmp_dir)
    assert run_git(
        'commit',
        '-m',
        'remove regular library directory',
        '--',
        'Model/LibSubModule',
        dir=tmp_dir,
    )
    result = subprocess.run(
        [
            'git',
            '-c',
            'protocol.file.allow=always',
            'submodule',
            'add',
            str(submodule_repo_dir.resolve()),
            'Model/LibSubModule',
        ],
        cwd=str(tmp_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert run_git(
        'commit',
        '-m',
        'add library submodule',
        '--',
        '.gitmodules',
        'Model/LibSubModule',
        dir=tmp_dir,
    )

    project_path = model_dir / 'Model.etp'
    client.refresh(str(project_path))

    return tmp_dir


@pytest.fixture(scope='function', params=['model_repo', 'model_repo_with_submodule'])
def model_repository(request):
    """Provide the model with either a regular library directory or a submodule."""
    return request.getfixturevalue(request.param)


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
    (core.CmdCommit(_test_ide), 'commit.json', []),
]


@pytest.mark.usefixtures('model_repository')
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
    if core._git_client.submodules_paths:
        submodule_name = '<FileRef> Model/LibSubModule/LibSubModule.etp'

        def remove_submodule_entry(browser):
            if isinstance(browser, dict):
                children = browser.get('children')
                if isinstance(children, list):
                    browser['children'] = [
                        child for child in children if child.get('name') != submodule_name
                    ]
                    for child in browser['children']:
                        remove_submodule_entry(child)

        expected_browser = json.loads((get_ref_dir() / ref).read_text())
        actual_browser = json.loads(result.read_text())
        remove_submodule_entry(expected_browser)
        remove_submodule_entry(actual_browser)
        assert actual_browser == expected_browser
    else:
        # Ignore the version number.
        diff = cmp_file(get_ref_dir() / ref, result, n=0)
        for line in list(diff):
            print(line, end='')
        captured = capsys.readouterr()
        assert captured.out == ''


@pytest.mark.usefixtures('model_repository')
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


@pytest.mark.usefixtures('model_repository')
@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_commit(capsys):
    """Test CmdDiff selecting a commit version."""

    class CmdDiffCommit(core.CmdDiff):
        def select_diff_version(self):
            return [1, 0]  # Commits, first commit

    cmd = CmdDiffCommit(_test_ide)
    assert cmd.on_enable()

    captured = capsys.readouterr()
    cmd.on_activate()
    captured = capsys.readouterr()
    lines = captured.out.strip().split('\n')
    assert len(lines) == 2
    archive = Path(lines[1].strip())
    assert archive.exists()


@pytest.mark.repo(get_resources_dir())
@pytest.mark.parametrize('version_type', [0, 1], ids=['branch', 'commit'])
def test_git_ext_core_diff_exports_recorded_submodule(
    model_repo_with_submodule, monkeypatch, tmp_path, capsys, version_type
):
    """Export the submodule revision recorded in the selected superproject version."""
    assert core._git_client is not None
    submodule = model_repo_with_submodule / 'Model' / 'LibSubModule'
    source = submodule / 'LibOp1.xscade'
    recorded = subprocess.run(
        ['git', 'show', 'HEAD:LibOp1.xscade'], cwd=submodule, capture_output=True, check=True
    ).stdout
    source.write_bytes(b'later submodule commit')
    subprocess.run(['git', 'add', 'LibOp1.xscade'], cwd=submodule, check=True)
    subprocess.run(
        [
            'git',
            '-c',
            'user.name=Test',
            '-c',
            'user.email=test@example.com',
            'commit',
            '-m',
            'later submodule commit',
        ],
        cwd=submodule,
        capture_output=True,
        check=True,
    )
    source.write_bytes(b'changed working tree')
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    monkeypatch.setattr(core._git_client, 'get_branch_list', lambda: ['tests'])
    commit_id = subprocess.run(
        ['git', 'rev-parse', 'HEAD'],
        cwd=model_repo_with_submodule,
        capture_output=True,
        check=True,
    ).stdout.strip()
    monkeypatch.setattr(core._git_client, 'get_commits_list', lambda: [(commit_id, 0)])

    class SelectVersion(core.CmdDiff):
        def select_diff_version(self):
            return [version_type, 0]

    capsys.readouterr()
    SelectVersion(_test_ide).on_activate()
    output = capsys.readouterr().out
    project = Path(output.strip().split('\n')[-1].strip())
    assert project.is_file()
    assert (project.parent / 'LibSubModule' / 'LibOp1.xscade').read_bytes() == recorded
    assert not (project.parent / 'LibSubModule' / '.git').exists()


@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_exports_nested_submodules(
    model_repo_with_submodule, monkeypatch, tmp_path, capsys
):
    """Export a submodule nested inside another submodule."""
    assert core._git_client is not None
    submodule = model_repo_with_submodule / 'Model' / 'LibSubModule'
    nested_repo = tmp_path / 'nested_repo'
    nested_repo.mkdir()

    def git(cwd, *args):
        subprocess.run(
            ['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', *args],
            cwd=cwd,
            capture_output=True,
            check=True,
        )

    git(nested_repo, 'init', '-b', 'main')
    (nested_repo / 'nested.txt').write_text('recorded nested content', encoding='utf-8')
    git(nested_repo, 'add', 'nested.txt')
    git(nested_repo, 'commit', '-m', 'nested initial commit')
    git(submodule, '-c', 'protocol.file.allow=always', 'submodule', 'add', str(nested_repo), 'nested')
    git(submodule, 'commit', '-m', 'add nested submodule')
    submodule_path = str(Path('Model') / 'LibSubModule')
    git(model_repo_with_submodule, 'add', submodule_path)
    git(model_repo_with_submodule, 'commit', '-m', 'update submodule', '--', submodule_path)
    (submodule / 'nested' / 'nested.txt').write_text('local change', encoding='utf-8')
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    monkeypatch.setattr(core._git_client, 'get_branch_list', lambda: ['tests'])
    capsys.readouterr()

    core.CmdDiff(_test_ide).on_activate()
    project = Path(capsys.readouterr().out.strip().split('\n')[-1].strip())
    nested_file = project.parent / 'LibSubModule' / 'nested' / 'nested.txt'
    assert nested_file.read_text(encoding='utf-8') == 'recorded nested content'
    assert not (nested_file.parent / '.git').exists()


@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_reuses_available_nested_submodule_commit(
    model_repo_with_submodule, monkeypatch, tmp_path, capsys
):
    """Export an uninitialized nested submodule from an available local commit."""
    assert core._git_client is not None
    submodule = model_repo_with_submodule / 'Model' / 'LibSubModule'
    remote = model_repo_with_submodule.parent / 'LibSubModuleRepo'

    def git(cwd, *args):
        return subprocess.run(
            ['git', '-c', 'user.name=Test', '-c', 'user.email=test@example.com', *args],
            cwd=cwd,
            capture_output=True,
            check=True,
        )

    recorded = git(submodule, 'show', 'HEAD:LibOp1.xscade').stdout
    git(submodule, '-c', 'protocol.file.allow=always', 'submodule', 'add', str(remote), 'nested')
    git(submodule, 'commit', '-m', 'add nested submodule')
    submodule_path = str(Path('Model') / 'LibSubModule')
    git(model_repo_with_submodule, 'add', submodule_path)
    git(model_repo_with_submodule, 'commit', '-m', 'update submodule', '--', submodule_path)
    (submodule / 'nested' / '.git').unlink()
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    monkeypatch.setattr(core._git_client, 'get_branch_list', lambda: ['tests'])
    capsys.readouterr()

    core.CmdDiff(_test_ide).on_activate()
    output = capsys.readouterr().out
    assert 'Launch the Diff Analyzer' in output
    project = Path(output.strip().split('\n')[-1].strip())
    assert (project.parent / 'LibSubModule' / 'nested' / 'LibOp1.xscade').read_bytes() == recorded


@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_normalizes_submodule_gitfile_path(
    model_repo_with_submodule, monkeypatch, tmp_path, capsys
):
    """Avoid opening pack indexes through unnecessarily long relative gitdir paths."""
    assert core._git_client is not None
    submodule = model_repo_with_submodule / 'Model' / 'LibSubModule'
    subprocess.run(['git', 'repack', '-a', '-d'], cwd=submodule, capture_output=True, check=True)
    original_open = builtins.open

    def legacy_open(file, *args, **kwargs):
        if isinstance(file, (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(file))
            if path.suffix == '.idx' and '..' in path.parts:
                raise FileNotFoundError('Unnormalized pack index path')
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, 'open', legacy_open)
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    monkeypatch.setattr(core._git_client, 'get_branch_list', lambda: ['tests'])
    capsys.readouterr()

    core.CmdDiff(_test_ide).on_activate()
    output = capsys.readouterr().out
    assert 'Launch the Diff Analyzer' in output
    project = Path(output.strip().split('\n')[-1].strip())
    assert (project.parent / 'LibSubModule' / 'LibOp1.xscade').is_file()


@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_missing_submodule_is_not_reported_as_success(
    model_repo_with_submodule, monkeypatch, tmp_path, capsys
):
    """Do not offer an incomplete export when the recorded submodule is unavailable."""
    assert core._git_client is not None
    submodule = model_repo_with_submodule / 'Model' / 'LibSubModule'
    (submodule / '.git').unlink()
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    monkeypatch.setattr(core._git_client, 'get_branch_list', lambda: ['tests'])
    capsys.readouterr()

    core.CmdDiff(_test_ide).on_activate()
    output = capsys.readouterr().out

    assert 'submodule' in output.lower()
    assert 'Launch the Diff Analyzer' not in output


@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_reports_unavailable_submodule_commit(
    model_repo_with_submodule, monkeypatch, tmp_path, capsys
):
    """Do not substitute a different commit when the recorded one is missing."""
    assert core._git_client is not None
    missing_commit = '1' * 40
    submodule_path = (Path('Model') / 'LibSubModule').as_posix()
    subprocess.run(
        ['git', 'update-index', '--cacheinfo', '160000', missing_commit, submodule_path],
        cwd=model_repo_with_submodule,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        [
            'git',
            '-c',
            'user.name=Test',
            '-c',
            'user.email=test@example.com',
            'commit',
            '-m',
            'record missing submodule commit',
        ],
        cwd=model_repo_with_submodule,
        capture_output=True,
        check=True,
    )
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    monkeypatch.setattr(core._git_client, 'get_branch_list', lambda: ['tests'])
    capsys.readouterr()

    core.CmdDiff(_test_ide).on_activate()
    output = capsys.readouterr().out
    assert missing_commit in output
    assert 'Launch the Diff Analyzer' not in output


@pytest.fixture
def git_extension(monkeypatch):
    """Load the GUI extension with stand-ins for the Studio-only APIs."""
    commands = ModuleType('scade.tool.suite.gui.commands')
    commands.ContextMenu = commands.Menu = commands.Toolbar = Mock()
    dialogs = ModuleType('scade.tool.suite.gui.dialogs')

    class Dialog:
        def __init__(self, name, width, height):
            pass

        def close(self):
            pass

    dialogs.Dialog = Dialog
    dialogs.message_box = Mock()
    widgets = ModuleType('scade.tool.suite.gui.widgets')
    widgets.Button = widgets.EditBox = widgets.ListBox = Mock()
    studio = ModuleType('ansys.scade.guitools.studio')
    studio.studio = _test_ide
    for module in (commands, dialogs, widgets, studio):
        monkeypatch.setitem(sys.modules, module.__name__, module)
    monkeypatch.setattr(core.GitClient, 'get_init_status', lambda self: False)
    monkeypatch.setattr(core, 'set_git_client', lambda client: None)
    monkeypatch.setattr(scade, 'tabput', lambda *args: None, raising=False)
    path = Path(core.__file__).with_name('gitextension.py')
    spec = importlib.util.spec_from_file_location('test_gitextension_module', path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.usefixtures('model_repo')
@pytest.mark.repo(get_resources_dir())
@pytest.mark.parametrize('version_type', [0, 1])
def test_gui_diff_selects_requested_version(git_extension, monkeypatch, tmp_path, version_type):
    """The GUI opens a dialog and exports the selected branch or commit."""
    assert core._git_client is not None
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    export = Mock(wraps=core._git_client.export_to_directory)
    monkeypatch.setattr(core._git_client, 'export_to_directory', export)

    def select_version(dialog):
        dialog.on_build()
        assert git_extension.ListBox.call_args.args[1] == dialog.items
        index = 1 if version_type == 0 else len(dialog.versions[0][1])
        selected = SimpleNamespace(get_selection=lambda: [dialog.items[index]])
        dialog.on_list_version_selection(selected, [index])
        dialog.on_close_click(None)

    monkeypatch.setattr(git_extension.SelectVersionDialog, 'do_modal', select_version, raising=False)
    cmd = git_extension.CmdDiff(_test_ide)
    cmd.on_activate()

    expected = cmd.versions[0][1][1] if version_type == 0 else cmd.commits_id[0]
    export.assert_called_once()
    assert export.call_args.args[0] == expected


def test_gui_diff_distinguishes_duplicate_commit_labels(git_extension):
    """Identical abbreviated commit labels still select the intended commit."""
    dialog = git_extension.SelectVersionDialog(
        'Select Version', [('Branches', []), ('Commits', ['abc12345  date', 'abc12345  date'])]
    )
    selected = SimpleNamespace(get_selection=lambda: [dialog.items[1]])
    dialog.on_list_version_selection(selected, [1])
    dialog.on_close_click(None)
    assert dialog.selection == [1, 1]


@pytest.mark.usefixtures('model_repo')
@pytest.mark.repo(get_resources_dir())
@pytest.mark.parametrize('action', ['cancel', 'window_close', 'no_selection'])
def test_gui_diff_without_confirmation_does_not_export(git_extension, monkeypatch, action):
    """Cancel, closing the window, or confirming no selection must not export."""
    assert core._git_client is not None
    export = Mock()
    monkeypatch.setattr(core._git_client, 'export_to_directory', export)

    def close_dialog(dialog):
        dialog.on_build()
        if action != 'no_selection':
            selected = SimpleNamespace(get_selection=lambda: [dialog.items[0]])
            dialog.on_list_version_selection(selected, [0])
        if action == 'cancel':
            dialog.on_cancel_click(None)
        elif action == 'no_selection':
            dialog.on_close_click(None)

    monkeypatch.setattr(git_extension.SelectVersionDialog, 'do_modal', close_dialog, raising=False)
    git_extension.CmdDiff(_test_ide).on_activate()
    export.assert_not_called()


def test_create_temp_dir_replaces_existing_export(tmp_path, monkeypatch):
    """Repeated exports use the same directory and remove stale contents."""
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    folder = str(Path('SCADE') / 'git-diff' / 'repo' / 'release.1')
    old_dir = tmp_path / folder
    old_dir.mkdir(parents=True)
    old_file = old_dir / 'old.txt'
    old_file.write_text('previous export')

    first = core.create_temp_dir(folder)
    (first / 'new.txt').write_text('first export')
    second = core.create_temp_dir(folder)

    assert first == second == old_dir
    assert second.is_dir()
    assert not old_file.exists()
    assert not (first / 'new.txt').exists()


def test_create_temp_dir_no_deprecation_warning(tmp_path, monkeypatch):
    """Replacing an export does not use the deprecated arguments of shutil.rmtree."""
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    folder = str(Path('SCADE') / 'git-diff' / 'repo' / 'branch')
    old_dir = tmp_path / folder
    (old_dir / 'sub').mkdir(parents=True)
    (old_dir / 'sub' / 'old.txt').write_text('previous export')
    with warnings.catch_warnings():
        warnings.simplefilter('error', DeprecationWarning)
        assert core.create_temp_dir(folder) == old_dir
    assert not (old_dir / 'sub').exists()


@pytest.mark.skipif(os.name != 'nt', reason='Windows read-only file behavior')
def test_create_temp_dir_removes_read_only_files(tmp_path, monkeypatch):
    """A read-only file in an earlier export must not prevent replacement."""
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    folder = str(Path('SCADE') / 'git-diff' / 'repo' / 'branch')
    old_dir = tmp_path / folder
    old_dir.mkdir(parents=True)
    old_file = old_dir / 'old.txt'
    old_file.write_text('previous export')
    old_file.chmod(stat.S_IREAD)
    try:
        assert core.create_temp_dir(folder) == old_dir
        assert not old_file.exists()
    finally:
        if old_file.exists():
            old_file.chmod(stat.S_IWRITE)


@pytest.mark.skipif(os.name != 'nt', reason='Windows file locking behavior')
def test_create_temp_dir_reports_locked_files(tmp_path, monkeypatch):
    """A file that cannot be removed must report the original cleanup error."""
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    folder = str(Path('SCADE') / 'git-diff' / 'repo' / 'branch')
    old_dir = tmp_path / folder
    old_dir.mkdir(parents=True)
    old_file = old_dir / 'old.txt'
    old_file.write_text('previous export')

    with old_file.open('r'):
        with pytest.raises(PermissionError):
            core.create_temp_dir(folder)


@pytest.mark.usefixtures('model_repo')
@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_repeated_dotted_branch(capsys, tmp_path, monkeypatch):
    """Repeated diffs on a dotted branch replace the previous exported project."""
    assert core._git_client is not None
    run_git('branch', 'release.1', dir=core._git_client.repo_path)
    monkeypatch.setattr(core._git_client, 'get_branch_list', lambda: ['release.1'])
    monkeypatch.setattr(core.tempfile, 'gettempdir', lambda: str(tmp_path))
    cmd = core.CmdDiff(_test_ide)
    capsys.readouterr()

    cmd.on_activate()
    first = Path(capsys.readouterr().out.strip().split('\n')[-1].strip())
    first.write_text('stale export')
    cmd.on_activate()
    second = Path(capsys.readouterr().out.strip().split('\n')[-1].strip())

    assert first == second
    assert second.is_file()
    assert second.read_text() != 'stale export'
    assert not list(tmp_path.rglob('*.tar'))


@pytest.mark.usefixtures('model_repository')
@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_cancel(capsys):
    """Test CmdDiff when the user cancels version selection."""

    class CmdDiffCancel(core.CmdDiff):
        def select_diff_version(self):
            return [-1, -1]

    cmd = CmdDiffCancel(_test_ide)
    assert cmd.on_enable()

    captured = capsys.readouterr()
    cmd.on_activate()
    captured = capsys.readouterr()
    assert 'Diff cancelled' in captured.out


@pytest.mark.usefixtures('model_repository')
@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_commit_nothing_staged(capsys):
    """Test CmdCommit when there is nothing to commit."""
    asked = []

    class CmdCommitSpy(core.CmdCommit):
        def get_commit_text(self):
            asked.append(True)
            return 'some message'

    cmd = CmdCommitSpy(_test_ide)
    assert cmd.on_enable()
    cmd.on_activate()
    assert asked
    repo = core._git_client.repo
    head = repo.head()

    # the first commit empties the index: the second one is refused, without any prompt
    asked.clear()
    capsys.readouterr()
    cmd.on_activate()
    assert 'Nothing to commit' in capsys.readouterr().out
    assert not asked
    assert repo.head() == head


class _Project:
    """Minimal SCADE project, the Diff command only uses its path."""

    def __init__(self, pathname: str):
        self.pathname = pathname


@pytest.mark.usefixtures('model_repository')
@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_diff_active_project(capsys, monkeypatch):
    """Test CmdDiff exports the active project, not the first loaded one."""
    assert core._git_client is not None
    active = _test_ide.get_active_project()
    other = _Project(str(Path(core._git_client.repo_path) / 'Other' / 'Other.etp'))
    monkeypatch.setattr(_test_ide, 'get_projects', lambda: [other, active])
    monkeypatch.setattr(_test_ide, 'get_active_project', lambda: active)

    capsys.readouterr()
    core.CmdDiff(_test_ide).on_activate()
    output = capsys.readouterr().out
    assert 'Launch the Diff Analyzer tool with the project' in output
    assert Path(output.strip().split('\n')[-1].strip()).name == 'Model.etp'


@pytest.mark.usefixtures('model_repository')
@pytest.mark.repo(get_resources_dir())
@pytest.mark.parametrize('location', ['outside', 'none'])
def test_git_ext_core_diff_project_not_in_repo(capsys, monkeypatch, tmp_path, location):
    """Test CmdDiff when there is no active project or it is not in the repository."""
    asked = []

    class CmdDiffSpy(core.CmdDiff):
        def select_diff_version(self):
            asked.append(True)
            return [0, 0]

    project = _Project(str(tmp_path / 'Other' / 'Other.etp')) if location == 'outside' else None
    monkeypatch.setattr(_test_ide, 'get_active_project', lambda: project)

    capsys.readouterr()
    CmdDiffSpy(_test_ide).on_activate()
    output = capsys.readouterr().out
    # nothing is asked to the user, and nothing is exported
    assert not asked
    assert 'Diff cancelled' in output
    assert 'is not in the Git repository' in output or 'no project loaded' in output
    assert 'Launch the Diff Analyzer' not in output


@pytest.mark.usefixtures('model_repository')
@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_refresh_submodule_paths_detected(capsys):
    """Verify submodule paths are properly detected by GitClient."""
    # In the model_repo fixture, LibSubModule is just a regular directory
    # This test verifies the submodule detection mechanism works
    assert core._git_client is not None

    # Get the submodule paths (will be empty in model_repo since it's not a real submodule)
    submodule_paths = core._git_client.submodules_paths
    # Just verify that the property exists and can be accessed
    assert isinstance(submodule_paths, list)


@pytest.mark.repo(get_resources_dir())
def test_git_ext_core_submodule_fixture_available(model_repo_with_submodule):
    """Verify LibSubModule is a real submodule in the model repository."""
    tmp_dir = model_repo_with_submodule
    submodule_dir = tmp_dir / 'Model' / 'LibSubModule'

    assert (tmp_dir / '.gitmodules').is_file()
    assert submodule_dir.is_dir()
    assert (submodule_dir / 'LibSubModule.etp').is_file()
    assert core._git_client is not None
    assert submodule_dir.resolve() in core._git_client.submodules_paths
