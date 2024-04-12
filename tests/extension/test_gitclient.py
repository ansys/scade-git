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

from pathlib import Path
from shutil import copytree

import pytest

from ansys.scade.git.extension.gitclient import GitClient, GitStatus
from test_utils import get_resources_dir as get_tests_dir, run_git

# local constants for conciseness
ADDED = GitStatus.added
REMOVED_STAGED = GitStatus.removed_staged
MODIFIED_STAGED = GitStatus.modified_staged
REMOVED_UNSTAGED = GitStatus.removed_unstaged
MODIFIED_UNSTAGED = GitStatus.modified_unstaged
UNTRACKED = GitStatus.untracked
CLEAN = GitStatus.clean
EXTERN = GitStatus.extern


class TestGitClient(GitClient):
    def log(self, text):
        """Print the logs to the standard output."""
        print(text)


def get_resources_dir() -> Path:
    """Return the resources directory for these tests."""
    return get_tests_dir() / 'extension' / 'resources'


@pytest.fixture(scope='class')
def tmp_repo(request, tmpdir_factory):
    """
    Initializes a GitClient for a test repository.

    A temporary git repo is created from the directory containing the project.
    """
    # behaves as a __init__ method for request.cls
    marker = request.node.get_closest_marker('project')
    # marker is None if the test is not designed correctly
    assert marker
    path = marker.args[0]
    tmp_repos = Path(tmpdir_factory.mktemp('repos'))
    tmp_dir = tmp_repos / path.parent.name
    copytree(path.parent, tmp_dir)
    # create git repo and add all files
    run_git('init', '-b', 'main', str(tmp_dir))
    # runt the next commands in the context of the git repo
    run_git('add', str(tmp_dir), dir=tmp_dir)
    run_git('commit', '-m', 'copy', dir=tmp_dir)

    # store the temporary paths in the test class instance
    request.cls.dir = tmp_dir
    request.cls.project_path = str(request.cls.dir / path.name)

    # get the instance of GitClient
    request.cls.git_client = TestGitClient()
    status = request.cls.git_client.get_init_status()
    assert status
    status = request.cls.git_client.refresh(request.cls.project_path)
    assert status


@pytest.mark.project(get_resources_dir() / 'Model' / 'Model.etp')
@pytest.mark.usefixtures('tmp_repo')
class TestGitClientNominal:
    """Nominal tests for GitClient."""
    file_data = [
        (['Model.etp', CLEAN]),
        (['C:/Program Files/ANSYS Inc/v241/SCADE/SCADE/libraries/SC65/libdigital/libdigital.etp', EXTERN]),
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
        if absolute and not Path(path).absolute():
            # path is expected to be relative to the repository
            path = str(self.dir / path)
        _, status = self.git_client.get_file_status(path)
        assert status == expected

    def test_status_untracked(self):
        # create a new file
        path = self.dir / 'untracked_file.txt'
        path.open('w').write('some content\n')
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == UNTRACKED
        path.unlink()

    def test_status_added(self):
        # create a new file
        path = self.dir / 'new_file.txt'
        path.open('w').write('some content\n')
        self.git_client.stage([str(path)])
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == ADDED

    def test_status_modified_unstaged(self):
        # modify a file
        path = self.dir / 'modified_unstaged.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.open('w').write('new content\n')
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_UNSTAGED
        # revert
        self.git_client.reset_files([str(path)])
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN

    def test_status_modified_staged(self):
        # modify a file
        path = self.dir / 'modified_staged.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.open('w').write('new content\n')
        self.git_client.stage([str(path)])
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_STAGED
        # revert
        self.git_client.unstage([str(path)])
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_UNSTAGED

    def test_status_removed_unstaged(self):
        # modify a file
        path = self.dir / 'removed_unstaged.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.unlink()
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == REMOVED_UNSTAGED

    def test_status_removed_staged(self):
        # modify a file, using a relative path to exercise stage and unstage
        # path = self.dir / 'removed_staged.txt'
        path = Path('removed_staged.txt')
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.unlink()
        self.git_client.stage([str(path)])
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == REMOVED_STAGED
        self.git_client.unstage([str(path)])
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == REMOVED_UNSTAGED

    def test_reset(self):
        # modify a file and reset the changes
        path = self.dir / 'reset.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.open('w').write('new content\n')
        self.git_client.stage([str(path)])
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_STAGED
        self.git_client.reset()
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN

    def test_commit(self):
        # modify a file and commit the changes
        path = self.dir / 'commit.txt'
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN
        path.open('w').write('new content\n')
        self.git_client.stage([str(path)])
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == MODIFIED_STAGED
        self.git_client.commit('some text')
        self.git_client.refresh(self.project_path)
        _, status = self.git_client.get_file_status(str(path))
        assert status == CLEAN

    def test_branch_list(self):
        # basic test: make sure the branch 'main' is present
        branches = self.git_client.get_branch_list()
        assert 'main' in branches

    def test_archive(self, tmpdir):
        # add any file
        output = tmpdir / 'Archive.tar.gz'
        status = self.git_client.archive('main', str(output))
        assert status
        assert output.exists()


# unexisting project in the parent of the repository
@pytest.mark.project(get_resources_dir() / 'Model' / 'Model.etp')
@pytest.mark.usefixtures('tmp_repo')
class TestGitClientRobustnessWrongArgs:
    """
    Verify GitClient does not raise exception with invalid parameters.

    Note: The tests are using absolute and relative paths.
    """
    def test_get_file_status(self):
        # unexisting file
        path = Path('Unknown.txt')
        _, status = self.git_client.get_file_status(path)
        assert status == UNTRACKED
        path = self.dir / path.name
        _, status = self.git_client.get_file_status(path)
        assert status == UNTRACKED

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
        output = tmpdir / 'InvalidArchive.tar.gz'
        status = self.git_client.archive('<wrong branch>', str(output))
        # no exception
        assert not status


@pytest.fixture(scope='class')
def wrong_repo(request, tmpdir_factory):
    """Initializes a GitClient for a test directory which is not tracked."""
    # behaves as a __init__ method for request.cls
    marker = request.node.get_closest_marker('project')
    # marker is None if the test is not designed correctly
    assert marker
    path = marker.args[0]
    tmp_repos = Path(tmpdir_factory.mktemp('repos'))
    tmp_dir = tmp_repos / path.parent.name
    copytree(path.parent, tmp_dir)

    # store the temporary paths in the test class instance
    request.cls.dir = tmp_dir
    request.cls.project_path = str(request.cls.dir / path.name)

    # get the instance of GitClient
    request.cls.git_client = TestGitClient()
    status = request.cls.git_client.get_init_status()
    assert status
    status = request.cls.git_client.refresh(request.cls.project_path)
    assert not status


@pytest.mark.project(get_resources_dir() / 'Model' / 'Model.etp')
@pytest.mark.usefixtures('wrong_repo')
class TestGitClientRobustnessWrongRepo:
    """Verify GitClient does not raise exception with invalid repository."""
    def test_get_file_status(self):
        path = self.dir / 'Model.etp'
        _, status = self.git_client.get_file_status(path)
        assert status is None

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
        # add any file
        output = tmpdir / 'NotProduced.tar.gz'
        status = self.git_client.archive('HEAD', str(output))
        # no exception
        assert not status
        assert not output.exists()

    def test_branch_list(self):
        branches = self.git_client.get_branch_list()
        assert branches == []
