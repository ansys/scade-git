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

# Design note: linter complains about unexisting git_client and dir attributes
# for test classes: these attributes are added dynamically to the instances
# by cls_tmp_repo and cls_git_repo fixtures
# workaround: use 'getattr', or add 'type: ignore' pragma --> too verbose

import os
from pathlib import Path
from subprocess import run
import sys
from typing import List, Tuple

import pytest

from ansys.scade.git.extension.gitclient import GitClient, GitStatus, find_git_repo
from test_utils import get_resources_dir as get_tests_dir

# local constants for conciseness
ADDED = GitStatus.added
REMOVED_STAGED = GitStatus.removed_staged
MODIFIED_STAGED = GitStatus.modified_staged
REMOVED_UNSTAGED = GitStatus.removed_unstaged
MODIFIED_UNSTAGED = GitStatus.modified_unstaged
UNTRACKED = GitStatus.untracked
CLEAN = GitStatus.clean
EXTERN = GitStatus.extern
ERROR = GitStatus.error
NONE = GitStatus.none


def get_resources_dir() -> Path:
    """Return the resources directory for these tests."""
    return get_tests_dir() / 'extension' / 'resources'


@pytest.fixture(scope='class')
def cls_tmp_repo(request, tmp_repo: Tuple[str, GitClient]):
    """Initialize the test class with the fixture data."""
    request.cls.dir, request.cls.git_client = tmp_repo


@pytest.fixture(scope='class')
def cls_git_repo(request, git_repo: Tuple[str, GitClient]):
    """Initialize the test class with the fixture data."""
    request.cls.dir, request.cls.git_client = git_repo


@pytest.mark.repo(get_resources_dir() / 'Model')
@pytest.mark.usefixtures('cls_git_repo')
class TestGitClientNominal:
    """Nominal tests for GitClient."""

    file_data = [
        (['Model.etp', CLEAN]),
        (
            [
                'C:/Program Files/ANSYS Inc/v241/SCADE/SCADE/libraries/SC65/libdigital/libdigital.etp',  # noqa: E501
                EXTERN,
            ]
        ),
        (['Root.xscade', CLEAN]),
        (['Child/Child.xscade', CLEAN]),
        (['P.xscade', CLEAN]),
        (['Model.l4', CLEAN]),
        # Sibling not in the temporary repository
        # (['/Sibling/Macros.h', CLEAN]),
    ]

    @pytest.mark.parametrize(
        'absolute',
        [False, True],
    )
    @pytest.mark.parametrize(
        'path, expected',
        file_data,
        ids=[Path(_[0]).name for _ in file_data],
    )
    def test_get_file_status(self, path: str, expected: GitStatus, absolute: bool):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        if absolute and not Path(path).absolute():
            # path is expected to be relative to the repository
            path = str(self.dir / path)
        _, status = self.git_client.get_file_status(path)
        assert status == expected

    def test_status_untracked(self):
        project_path = str(self.dir / 'Model.etp')
        # create a new file
        path = self.dir / 'untracked_file.txt'
        path.open('w').write('some content\n')
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == UNTRACKED
        path.unlink()

    def test_status_added(self):
        project_path = str(self.dir / 'Model.etp')
        self.git_client.refresh(project_path)
        # create a new file
        path = self.dir / 'new_file.txt'
        path.open('w').write('some content\n')
        self.git_client.stage([str(path)])
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == ADDED

    def test_status_modified_unstaged(self):
        project_path = str(self.dir / 'Model.etp')
        self.git_client.refresh(project_path)
        # modify a file
        path = self.dir / 'modified_unstaged.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.open('w').write('new content\n')
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_UNSTAGED
        # revert
        self.git_client.reset_files([str(path)])
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN

    def test_status_modified_staged(self):
        project_path = str(self.dir / 'Model.etp')
        self.git_client.refresh(project_path)
        # modify a file
        path = self.dir / 'modified_staged.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.open('w').write('new content\n')
        self.git_client.stage([str(path)])
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_STAGED
        # revert
        self.git_client.unstage([str(path)])
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_UNSTAGED

    def test_status_removed_unstaged(self):
        project_path = str(self.dir / 'Model.etp')
        self.git_client.refresh(project_path)
        # modify a file
        path = self.dir / 'removed_unstaged.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.unlink()
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == REMOVED_UNSTAGED

    def test_status_removed_staged(self):
        project_path = str(self.dir / 'Model.etp')
        self.git_client.refresh(project_path)
        # modify a file, using a relative path to exercise stage and unstage
        # path = self.dir / 'removed_staged.txt'
        path = Path('removed_staged.txt')
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        # the paths relative to the repository do not depend on the current directory
        (self.dir / path).unlink()
        self.git_client.stage([str(path)])
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == REMOVED_STAGED
        self.git_client.unstage([str(path)])
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == REMOVED_UNSTAGED

    def test_reset(self):
        project_path = str(self.dir / 'Model.etp')
        self.git_client.refresh(project_path)
        # modify a file and reset the changes
        path = self.dir / 'reset.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.open('w').write('new content\n')
        self.git_client.stage([str(path)])
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_STAGED
        self.git_client.reset()
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN

    def test_commit(self):
        project_path = str(self.dir / 'Model.etp')
        self.git_client.refresh(project_path)
        # modify a file and commit the changes
        path = self.dir / 'commit.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.open('w').write('new content\n')
        self.git_client.stage([str(path)])
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_STAGED
        self.git_client.commit('some text')
        self.git_client.refresh(project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN

    def test_branch_list(self):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        # basic test: make sure the branch 'main' is present
        branches = self.git_client.get_branch_list()
        assert 'main' in branches

    def test_commit_list(self):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        # basic test: make sure the commit 'xxxx' is present
        commits = self.git_client.get_commits_list()
        assert type(commits[0][0]) is bytes
        assert len(commits[0][0]) == 40
        assert commits[0][1] > 1765471530

    def test_archive(self, tmpdir):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        # add any file
        output = tmpdir / 'Archive.tar'
        status = self.git_client.archive('main', str(output))
        assert status
        assert output.exists()

    def test_export_to_directory(self, tmpdir):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        output = tmpdir / 'Export'
        status = self.git_client.export_to_directory('main', str(output))
        assert status
        assert output.exists()
        assert (output / 'Model.etp').exists()
        assert not (output / '.git').exists()


# unexisting project in the parent of the repository
@pytest.mark.repo(get_resources_dir() / 'Model')
@pytest.mark.usefixtures('cls_git_repo')
class TestGitClientRobustnessWrongArgs:
    """
    Verify GitClient does not raise exception with invalid parameters.

    Note: The tests are using absolute and relative paths.
    """

    def test_get_file_status(self):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        # unexisting file
        path = Path('Unknown.txt')
        _, status = self.git_client.get_file_status(path)
        assert status == ERROR
        path = self.dir / path.name
        _, status = self.git_client.get_file_status(path)
        assert status == ERROR

    def test_stage(self):
        # unexisting file
        path = Path('Unknown.txt')
        self.git_client.stage([str(path)])
        # no exception
        path = self.dir / path.name
        self.git_client.stage([str(path)])
        # no exception

    def test_unstage(self):
        # unexisting file
        path = Path('Unknown.txt')
        self.git_client.unstage([str(path)])
        # no exception
        path = self.dir / path.name
        self.git_client.unstage([str(path)])
        # no exception

    def test_reset_files(self):
        # unexisting file
        path = Path('Unknown.txt')
        self.git_client.reset_files([str(path)])
        # no exception
        path = self.dir / path.name
        self.git_client.reset_files([str(path)])
        # no exception

    def test_archive(self, tmpdir):
        # add any file
        output = tmpdir / 'InvalidArchive.tar'
        status = self.git_client.archive('<wrong branch>', str(output))
        # no exception
        assert not status

    def test_export_to_directory(self, tmpdir):
        output = tmpdir / 'InvalidExport'
        status = self.git_client.export_to_directory('<wrong branch>', str(output))
        # no exception
        assert not status


@pytest.mark.repo(get_resources_dir() / 'Model')
@pytest.mark.usefixtures('cls_tmp_repo')
class TestGitClientRobustnessWrongRepo:
    """Verify GitClient does not raise exception with invalid repository."""

    def test_get_file_status(self):
        path = self.dir / 'Model.etp'
        self.git_client.refresh(str(path))
        _, status = self.git_client.get_file_status(path)
        assert status == NONE

    def test_stage(self):
        # add any file
        path = self.dir / 'Model.etp'
        self.git_client.stage([str(path)])
        # no exception

    def test_unstage(self):
        # add any file
        path = self.dir / 'Model.etp'
        self.git_client.unstage([str(path)])
        # no exception

    def test_reset_files(self):
        # add any file
        path = self.dir / 'Model.etp'
        self.git_client.reset_files([str(path)])
        # no exception

    def test_reset(self):
        # no parameter required
        self.git_client.reset()
        # no exception

    def test_commit(self):
        # commit any change
        self.git_client.commit('some text')
        # no exception

    def test_archive(self, tmpdir):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        # add any file
        output = tmpdir / 'NotProduced.tar'
        status = self.git_client.archive('HEAD', str(output))
        # no exception
        assert not status
        assert not output.exists()

    def test_export_to_directory(self, tmpdir):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        output = tmpdir / 'NotProducedExport'
        status = self.git_client.export_to_directory('HEAD', str(output))
        # no exception
        assert not status

    def test_branch_list(self):
        branches = self.git_client.get_branch_list()
        assert branches == []

    def test_commit_list(self):
        commits = self.git_client.get_commits_list()
        assert commits == []


class TestGitClientExportSubmodule:
    """Verify export_to_directory handles submodules."""

    class _Client(GitClient):
        def log(self, text: str):
            """Ignore logs in tests."""
            print(text)

    def _run_git(self, cwd: Path, *args: str):
        cp = run(['git', *args], cwd=str(cwd), capture_output=True, text=True)
        if cp.stdout:
            print(cp.stdout)
        if cp.stderr:
            print(cp.stderr)
        assert cp.returncode == 0

    def test_export_to_directory_submodule(self, tmp_path: Path):
        root_repo = tmp_path / 'root'
        sub_repo = tmp_path / 'subrepo'
        export_dir = tmp_path / 'export'

        root_repo.mkdir()
        sub_repo.mkdir()

        self._run_git(sub_repo, 'init', '-b', 'main')
        (sub_repo / 'sub.txt').write_text('submodule content\n', encoding='utf-8')
        self._run_git(sub_repo, 'add', 'sub.txt')
        self._run_git(
            sub_repo,
            '-c',
            'user.email=test@example.com',
            '-c',
            'user.name=test',
            'commit',
            '-m',
            'sub init',
        )

        self._run_git(root_repo, 'init', '-b', 'main')
        (root_repo / 'root.txt').write_text('root content\n', encoding='utf-8')
        self._run_git(root_repo, 'add', 'root.txt')
        self._run_git(
            root_repo,
            '-c',
            'user.email=test@example.com',
            '-c',
            'user.name=test',
            'commit',
            '-m',
            'root init',
        )

        self._run_git(
            root_repo,
            '-c',
            'protocol.file.allow=always',
            'submodule',
            'add',
            str(sub_repo),
            'deps/sub',
        )
        self._run_git(
            root_repo,
            '-c',
            'user.email=test@example.com',
            '-c',
            'user.name=test',
            'commit',
            '-m',
            'add submodule',
        )

        client = self._Client()
        status = client.refresh(str(root_repo / 'root.txt'))
        assert status

        exported = client.export_to_directory('main', str(export_dir))
        assert exported
        assert (export_dir / 'root.txt').read_text(encoding='utf-8') == 'root content\n'
        assert (export_dir / 'deps' / 'sub' / 'sub.txt').read_text(
            encoding='utf-8'
        ) == 'submodule content\n'
        assert not (export_dir / '.git').exists()
        assert not (export_dir / 'deps' / 'sub' / '.git').exists()


class TestGitClientSubmoduleFiles:
    """Verify the files of a submodule are not handled by the superproject."""

    class _Client(GitClient):
        def __init__(self):
            super().__init__()
            self.logs = []

        def log(self, text: str):
            """Store the logs."""
            self.logs.append(text)

    @staticmethod
    def _git(cwd: Path, *args: str) -> str:
        cmd = ['git', '-c', 'user.email=test@example.com', '-c', 'user.name=test']
        cmd += ['-c', 'protocol.file.allow=always', *args]
        cp = run(cmd, cwd=str(cwd), capture_output=True, text=True)
        assert cp.returncode == 0, cp.stderr
        return cp.stdout

    @pytest.fixture
    def client(self, tmp_path: Path) -> '_Client':
        sub_repo = tmp_path / 'subrepo'
        root_repo = tmp_path / 'root'
        for repo, name in [(sub_repo, 'sub.txt'), (root_repo, 'root.txt')]:
            repo.mkdir()
            self._git(repo, 'init', '-b', 'main')
            (repo / name).write_text(name, encoding='utf-8')
            self._git(repo, 'add', name)
            self._git(repo, 'commit', '-m', 'init')
        self._git(root_repo, 'submodule', 'add', str(sub_repo), 'deps/sub')
        self._git(root_repo, 'commit', '-m', 'add submodule')
        client = self._Client()
        assert client.refresh(str(root_repo / 'root.txt'))
        return client

    def _index(self, client: '_Client') -> List[str]:
        return self._git(Path(client.repo_path), 'ls-files').split()

    def test_is_inside_submodule(self, client: '_Client'):
        root = Path(client.repo_path)
        assert client.is_inside_submodule('deps/sub/sub.txt')
        assert client.is_inside_submodule(root / 'deps' / 'sub' / 'sub.txt')
        assert client.is_inside_submodule('deps/sub/new/file.txt')
        # the submodule itself can be staged by the superproject
        assert not client.is_inside_submodule('deps/sub')
        assert not client.is_inside_submodule('root.txt')
        assert not client.is_inside_submodule('deps/subother/file.txt')

    def test_stage_skips_submodule_files(self, client: '_Client'):
        root = Path(client.repo_path)
        (root / 'deps' / 'sub' / 'sub.txt').write_text('modified', encoding='utf-8')
        (root / 'other.txt').write_text('other', encoding='utf-8')
        client.stage(['deps/sub/sub.txt', str(root / 'other.txt')])
        # no regular entry is created below the gitlink
        assert self._index(client) == ['.gitmodules', 'deps/sub', 'other.txt', 'root.txt']
        assert any('Error stage: deps/sub/sub.txt belongs to a submodule' in _ for _ in client.logs)

    def test_stage_only_submodule_files(self, client: '_Client'):
        root = Path(client.repo_path)
        (root / 'deps' / 'sub' / 'sub.txt').write_text('modified', encoding='utf-8')
        client.stage(['deps/sub/sub.txt'])
        assert self._index(client) == ['.gitmodules', 'deps/sub', 'root.txt']

    def test_submodule_at_other_commit(self, client: '_Client'):
        root = Path(client.repo_path)
        submodule = root / 'deps' / 'sub'
        (submodule / 'sub.txt').write_text('v2', encoding='utf-8')
        self._git(submodule, 'add', 'sub.txt')
        self._git(submodule, 'commit', '-m', 'v2')
        assert client.refresh(client.repo_path)
        # the submodule is modified, not removed
        assert client.files_status['deps/sub'] == MODIFIED_UNSTAGED
        assert 'deps/sub' not in client.deleted

        # the pointer can be staged
        client.stage(['deps/sub'])
        assert self._index(client) == ['.gitmodules', 'deps/sub', 'root.txt']
        assert self._git(root, 'diff', '--cached', '--name-only').split() == ['deps/sub']

    @pytest.mark.parametrize('action', ['unstage', 'reset_files'])
    def test_unstage_reset_skip_submodule_files(self, client: '_Client', action: str):
        getattr(client, action)(['deps/sub/sub.txt'])
        name = 'unstage' if action == 'unstage' else 'reset'
        assert client.logs == [
            'Error {0}: deps/sub/sub.txt belongs to a submodule, '
            'use the Git repository of the submodule'.format(name)
        ]


class TestGitClientCommitsList:
    """Verify the list of commits."""

    class _Client(GitClient):
        def log(self, text: str):
            """Print the logs to the standard output."""
            print(text)

    @staticmethod
    def _fast_import(cwd: Path, script: str):
        cp = run(
            ['git', 'fast-import', '--quiet'],
            cwd=str(cwd),
            input=script.encode('ascii'),
            capture_output=True,
        )
        assert cp.returncode == 0, cp.stderr

    @staticmethod
    def _commit(ref: str, time: int, parent: str = '') -> str:
        # a commit without parent is added to the tip of the branch, if it exists
        committer = 'committer test <test@example.com> {0} +0000'.format(time)
        lines = ['commit {0}'.format(ref), committer, 'data 1', 'x']
        if parent:
            lines.append('from {0}'.format(parent))
        return '\n'.join(lines) + '\n\n'

    def test_long_history(self, tmp_path: Path):
        # longer than the recursion limit, and than the number of returned commits
        count = sys.getrecursionlimit() + 500
        run(['git', 'init', '-b', 'main'], cwd=str(tmp_path), check=True, capture_output=True)
        script = ''.join(self._commit('refs/heads/main', 1000000 + i) for i in range(count))
        self._fast_import(tmp_path, script)
        client = self._Client()
        assert client.refresh(str(tmp_path))
        commits = client.get_commits_list()
        assert len(commits) == 1000
        timestamps = [_[1] for _ in commits]
        assert timestamps == sorted(timestamps, reverse=True)
        assert timestamps[0] == 1000000 + count - 1

    def test_branches_share_commits(self, tmp_path: Path):
        run(['git', 'init', '-b', 'main'], cwd=str(tmp_path), check=True, capture_output=True)
        script = self._commit('refs/heads/main', 100)
        script += self._commit('refs/heads/main', 200)
        script += self._commit('refs/heads/other', 300, 'refs/heads/main')
        self._fast_import(tmp_path, script)
        client = self._Client()
        assert client.refresh(str(tmp_path))
        # the common commits are reported once
        assert [_[1] for _ in client.get_commits_list()] == [300, 200, 100]


class TestGitClientDetachedHead:
    """Verify refresh supports a detached HEAD."""

    class _Client(GitClient):
        def log(self, text: str):
            """Print the logs to the standard output."""
            print(text)

    @staticmethod
    def _git(cwd: Path, *args: str) -> str:
        cmd = ['git', '-c', 'user.email=test@example.com', '-c', 'user.name=test', *args]
        cp = run(cmd, cwd=str(cwd), capture_output=True, text=True)
        assert cp.returncode == 0, cp.stderr
        return cp.stdout.strip()

    @pytest.fixture
    def repo(self, tmp_path: Path) -> Path:
        self._git(tmp_path, 'init', '-b', 'main')
        for name in ['first.txt', 'second.txt']:
            (tmp_path / name).write_text(name, encoding='utf-8')
            self._git(tmp_path, 'add', name)
            self._git(tmp_path, 'commit', '-m', name)
        self._git(tmp_path, 'tag', 'v1', 'HEAD~1')
        return tmp_path

    def test_branch(self, repo: Path):
        client = self._Client()
        assert client.refresh(str(repo / 'first.txt'))
        assert client.branch == 'main'
        assert not client.detached

    @pytest.mark.parametrize('target', ['v1', 'HEAD~1'])
    def test_detached(self, repo: Path, target: str):
        sha = self._git(repo, 'rev-parse', target + '^{commit}')
        self._git(repo, 'checkout', '--detach', target)
        client = self._Client()
        assert client.refresh(str(repo / 'first.txt'))
        assert client.branch == 'HEAD detached at ' + sha[:7]
        assert client.detached
        assert client.files_status['first.txt'] == GitStatus.clean
        # the state is reset when the branch is checked out again
        self._git(repo, 'checkout', 'main')
        assert client.refresh(str(repo / 'first.txt'))
        assert client.branch == 'main'
        assert not client.detached


class TestGitClientStagedAndUnstaged:
    """Verify the status of the files changed again after being staged."""

    class _Client(GitClient):
        def log(self, text: str):
            """Print the logs to the standard output."""
            print(text)

    @pytest.fixture
    def client(self, tmp_path: Path) -> '_Client':
        def git(*args: str):
            cmd = ['git', '-c', 'user.email=test@example.com', '-c', 'user.name=test', *args]
            assert run(cmd, cwd=str(tmp_path), capture_output=True).returncode == 0

        git('init', '-b', 'main')
        (tmp_path / 'tracked.txt').write_text('v1', encoding='utf-8')
        git('add', 'tracked.txt')
        git('commit', '-m', 'init')
        client = self._Client()
        assert client.refresh(str(tmp_path / 'tracked.txt'))
        return client

    def _status(self, client: '_Client', name: str) -> GitStatus:
        assert client.refresh(client.repo_path)
        return client.get_file_status(name)[1]

    @pytest.mark.parametrize('name', ['tracked.txt', 'new.txt'])
    def test_modified_after_stage(self, client: '_Client', name: str):
        path = Path(client.repo_path) / name
        path.write_text('v2', encoding='utf-8')
        client.stage([name])
        staged = ADDED if name == 'new.txt' else MODIFIED_STAGED
        assert self._status(client, name) == staged
        # the file is modified again: the staged version is not the current one
        path.write_text('v3', encoding='utf-8')
        assert self._status(client, name) == MODIFIED_UNSTAGED
        # staging it again reports it as staged
        client.stage([name])
        assert self._status(client, name) == staged

    def test_removed_after_stage(self, client: '_Client'):
        path = Path(client.repo_path) / 'tracked.txt'
        path.write_text('v2', encoding='utf-8')
        client.stage(['tracked.txt'])
        path.unlink()
        assert self._status(client, 'tracked.txt') == REMOVED_UNSTAGED
        assert 'tracked.txt' in client.deleted

    @pytest.mark.skipif(sys.platform != 'win32', reason='case insensitive file system')
    def test_case_mismatch(self, client: '_Client', capsys):
        # the path of a file in a SCADE project can differ from the one in the index
        path = Path(client.repo_path) / 'tracked.txt'
        assert client.get_file_status('TRACKED.TXT') == ('tracked.txt', CLEAN)
        assert client.get_file_status(str(path).upper()) == ('tracked.txt', CLEAN)
        assert client.get_file_status('other.txt')[1] == GitStatus.error

        path.write_text('v2', encoding='utf-8')
        assert self._status(client, 'TRACKED.TXT') == MODIFIED_UNSTAGED
        capsys.readouterr()
        client.stage(['TRACKED.TXT'])
        assert self._status(client, 'tracked.txt') == MODIFIED_STAGED
        client.unstage(['TRACKED.TXT'])
        assert self._status(client, 'tracked.txt') == MODIFIED_UNSTAGED
        client.reset_files(['TRACKED.TXT'])
        assert self._status(client, 'tracked.txt') == CLEAN
        assert path.read_text(encoding='utf-8') == 'v1'
        # none of the commands reports an error
        assert 'Error' not in capsys.readouterr().out


class TestGitClientCommit:
    """Verify empty commits are refused."""

    class _Client(GitClient):
        def __init__(self):
            super().__init__()
            self.logs = []

        def log(self, text: str):
            """Store the logs."""
            self.logs.append(text)

    @pytest.fixture
    def client(self, tmp_path: Path) -> '_Client':
        cp = run(['git', 'init', '-b', 'main'], cwd=str(tmp_path), capture_output=True)
        assert cp.returncode == 0
        # commits are created by Dulwich: its author is read from the environment
        config = tmp_path / '.git' / 'config'
        config.write_text(
            config.read_text() + '[user]\n\tname = test\n\temail = test@example.com\n'
        )
        client = self._Client()
        assert client.refresh(str(tmp_path))
        return client

    def test_commit(self, client: '_Client'):
        path = Path(client.repo_path) / 'file.txt'
        # no commit yet, nothing staged
        assert not client.has_staged_changes()
        assert not client.commit('empty')
        assert client.logs[-1] == 'Error commit: nothing to commit, no staged changes'

        # initial commit, then a regular one
        for content in ['v1', 'v2']:
            path.write_text(content, encoding='utf-8')
            client.stage(['file.txt'])
            assert client.has_staged_changes()
            assert client.commit(content)
            assert not client.has_staged_changes()
        assert len(client.get_commits_list()) == 2

    def test_commit_unstaged_changes_only(self, client: '_Client'):
        path = Path(client.repo_path) / 'file.txt'
        path.write_text('v1', encoding='utf-8')
        client.stage(['file.txt'])
        assert client.commit('v1')
        head = client.repo.head()  # type: ignore
        path.write_text('v2', encoding='utf-8')
        assert not client.commit('v2')
        assert client.repo.head() == head  # type: ignore


class TestGitClientClose:
    """Verify the repository is released when it is not used anymore."""

    class _Client(GitClient):
        def log(self, text: str):
            """Print the logs to the standard output."""
            print(text)

    @pytest.fixture
    def client(self, tmp_path: Path) -> '_Client':
        cp = run(['git', 'init', '-b', 'main'], cwd=str(tmp_path), capture_output=True)
        assert cp.returncode == 0
        client = self._Client()
        assert client.refresh(str(tmp_path))
        return client

    @staticmethod
    def _spy_close(client: '_Client') -> List[bool]:
        closed = []
        repo = client.repo
        original = repo.close  # type: ignore
        repo.close = lambda: closed.append(True) or original()  # type: ignore
        return closed

    def test_refresh_closes_previous_repo(self, client: '_Client'):
        previous = client.repo
        closed = self._spy_close(client)
        assert client.refresh(client.repo_path)
        assert closed == [True]
        assert client.repo is not previous
        # the new repository is usable
        assert client.get_branch_list() == []

    def test_refresh_outside_repo_closes_repo(self, client: '_Client', tmp_path_factory):
        closed = self._spy_close(client)
        outside = tmp_path_factory.mktemp('outside')
        # find_git_repo is not influenced by a Git repository above the temporary directory
        if find_git_repo(str(outside)):
            pytest.skip('the temporary directory is in a Git repository')
        assert not client.refresh(str(outside))
        assert closed == [True]
        assert client.repo is None

    def test_close(self, client: '_Client'):
        closed = self._spy_close(client)
        client.close()
        assert closed == [True]
        assert client.repo is None
        # no error if the repository is already closed
        client.close()
        assert closed == [True]

    def test_refresh_keeps_current_directory(
        self, client: '_Client', tmp_path_factory, monkeypatch
    ):
        # the current directory of the process, shared with SCADE, is not modified
        elsewhere = tmp_path_factory.mktemp('elsewhere')
        monkeypatch.chdir(elsewhere)
        assert client.refresh(client.repo_path)
        assert os.path.samefile(os.getcwd(), str(elsewhere))
