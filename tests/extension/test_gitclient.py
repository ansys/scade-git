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

# Design note: linter complains about unexisting git_client and dir attributes
# for test classes: these attributes are added dynamically to the instances
# by cls_tmp_repo and cls_git_repo fixtures
# workaround: use 'getattr', or add 'type: ignore' pragma --> too verbose

from pathlib import Path
from typing import Tuple

import pytest

from ansys.scade.git.extension.gitclient import GitClient, GitStatus
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
        path.unlink()
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

    def test_archive(self, tmpdir):
        self.git_client.refresh(str(self.dir / 'Model.etp'))
        # add any file
        output = tmpdir / 'Archive.tar'
        status = self.git_client.archive('main', str(output))
        assert status
        assert output.exists()


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

    def test_branch_list(self):
        branches = self.git_client.get_branch_list()
        assert branches == []
