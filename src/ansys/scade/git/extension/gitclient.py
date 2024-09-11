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

"""Front-end for Git commands."""

from abc import ABCMeta, abstractmethod
from enum import Enum
import os
from pathlib import Path
import site
import sys
from typing import List, Tuple

# force user installed modules to have priority on Python installation
site_user = site.getusersitepackages()
if site_user in sys.path:
    sys.path.remove(site_user)
    sys.path.insert(1, site_user)

import dulwich as dulwich  # noqa: E402
from dulwich import porcelain as git  # noqa: E402
from dulwich.repo import Repo  # noqa: E402

# minimum Dulwich version
min_dulwich_ver = (0, 21, 3)

GitStatus = Enum(
    'GitStatus',
    [
        'added',
        'removed_staged',
        'modified_staged',
        'removed_unstaged',
        'modified_unstaged',
        'untracked',
        'clean',
        'extern',
        # status used for paths not present in the file system nor in the index
        'error',
    ],
)


def find_git_repo(local_proj_path: str) -> str:
    # repo – Path to the repository
    """
    Search ``local_proj_path`` directory and its parent directories for a git repository.

    Parameters
    ----------
    local_proj_path : str
        Path of the SCADE.

    Returns
    -------
    str
        Location of the git repository for this SCADE project, otherwise `None`.
    """
    # look for .git folders in local_proj_path or parent folders
    d = Path(local_proj_path)
    root = Path(d.root)
    disk = d.anchor

    while d != root and str(d) != disk:
        repo_path = d / '.git'
        if repo_path.is_dir():
            return str(d)
        d = d.parent

    return None


class GitClient(metaclass=ABCMeta):
    """Provide access to Git commands."""

    def __init__(self):
        self.repo_path = None
        self.repo_name = None
        self.branch = ''
        self.repo = None
        self.files_status = {}
        # check Dulwich version
        dulwich_ver = dulwich.__version__
        if dulwich_ver < min_dulwich_ver:
            self.log('Error: the Git extension is not correctly installed. It is disabled.')
            self.log(
                '   Dulwich (Git Python module) min version required: {0}, installed: {1}'.format(
                    min_dulwich_ver, dulwich_ver
                )
            )
            self.dulwich_ok = False
            # debug info
            for file in sys.path:
                self.log('sys path: {0}'.format(str(file)))
        else:
            self.dulwich_ok = True

    @abstractmethod
    def log(self, text: str):
        """
        Log a message.

        Parameters
        ----------
        text : str
            Message to display.
        """
        raise NotImplementedError('Abstract method call')

    def get_init_status(self) -> bool:
        """
        Return the initialization status.

        Returns
        -------
        bool
        """
        return self.dulwich_ok

    def refresh(self, project_path: str) -> bool:
        """
        Get the status of the files for the input project.

        Parameters
        ----------
        project_path : str
            Path of the SCADE project.

        Returns
        -------
        bool
        """
        self.files_status = {}
        if self.dulwich_ok:
            self.repo_path = find_git_repo(project_path)
        if self.repo_path:
            path_repo = Path(self.repo_path)
            self.repo_name = str(path_repo.name)
            os.chdir(self.repo_path)
            self.repo = Repo(self.repo_path)
            ref_chain, _ = self.repo.refs.follow(b'HEAD')
            # active_branch not supported by dulwich prior 20
            self.branch = git.active_branch(self.repo).decode('utf-8')
            # self.branch = str(Path(str(ref_chain[1].decode('utf-8'))).relative_to('refs/heads').as_posix()) # noqa: E501

            # git status for the current repo
            staged, unstaged, untracked = git.status(self.repo)

            # list files & status in git repo
            repo_files = git.ls_files(self.repo)
            for file in repo_files:
                file_str = file.decode('utf-8')
                # ['added', 'removed_staged', 'modified_staged', 'modified_unstaged',
                # 'untracked', 'removed_unstaged', 'clean', 'extern']
                if file in staged['add']:
                    status = GitStatus.added
                # elif (file in staged['delete']):
                #    status = GitStatus.removed_staged
                elif file in staged['modify']:
                    status = GitStatus.modified_staged
                elif file in unstaged:
                    file_abs_path = path_repo / file_str
                    if file_abs_path.is_file():
                        status = GitStatus.modified_unstaged
                    else:
                        status = GitStatus.removed_unstaged
                # untracked files are not listed in ls_files
                # elif (file_str in untracked):
                #    status = GitStatus.untracked
                else:
                    status = GitStatus.clean
                self.files_status[file_str] = status

            # deleted staged files are not listed in ls_files
            for file in staged['delete']:
                file_str = file.decode('utf-8')
                status = GitStatus.removed_staged
                self.files_status[file_str] = status

            # untracked files are not listed in ls_files
            # untracked returned as str, Windows path in 19.13 but posix in 21.3
            for file_str in untracked:
                status = GitStatus.untracked
                self.files_status[file_str] = status

            return True
        else:
            self.repo_name = None
            self.branch = ''
            self.repo = None
            return False

    def get_branch_list(self) -> List[str]:
        """
        Return the list of the repository's branches.

        Returns
        -------
        List[str]
        """
        if self.repo_path:
            branches = git.branch_list(self.repo)
            branches = [x.decode('utf-8') for x in branches]
        else:
            branches = []
        return branches

    def get_file_status(self, file_path: str) -> Tuple[str, GitStatus]:
        """
        Return the Git status of a file.

        Parameters
        ----------
        file_path : str
            Input path, either absolute or relative to the Git repository.

        Returns
        -------
        Tuple[str, GitStatus]
        """
        if self.repo_path:
            try:
                path = Path(file_path)
                if path.is_absolute():
                    abspath = path
                    index_file_name = path.relative_to(self.repo_path).as_posix()
                else:
                    index_file_name = path.as_posix()
                    abspath = Path(self.repo_path) / path
                status = self.files_status.get(index_file_name, None)
                if not status:
                    self.log("not status: %s %s" % (abspath, abspath.exists()))
                    status = GitStatus.untracked if abspath.exists() else GitStatus.error
                return index_file_name, status
            except ValueError:
                return file_path, GitStatus.extern
        else:
            return None, None

    def stage(self, files: List[str]):
        """
        Add the input files to the Git index.

        Parameters
        ----------
        files : List[str]
            List of files to stage. The paths are either absolute or
            relative to the Git repository.
        """
        if self.repo:
            try:
                # porcelain.add accepts any paths, absolute or relative to the repo
                return git.add(self.repo, files)
            except BaseException as e:
                self.log('Error stage: .{0}'.format(e))

    def unstage(self, files: List[str]):
        """
        Remove the input from the Git index.

        Parameters
        ----------
        files : List[str]
            List of files to unstage. The paths are either absolute or
            relative to the Git repository.
        """
        if self.repo:
            for file in files:
                try:
                    # repo.unstage only accepts relative paths to the repo path
                    file_path = Path(file)
                    if file_path.is_absolute():
                        index_file = file_path.relative_to(self.repo_path).as_posix()
                    else:
                        index_file = file
                    self.repo.unstage([index_file])
                except BaseException as e:
                    self.log('Error unstage: {0}'.format(e))

    def reset_files(self, files: List[str]):
        """
        Discard the changes of the input files.

        Parameters
        ----------
        files : List[str]
            List of files to unstage. The paths are either absolute or
            relative to the Git repository.
        """
        if self.repo:
            for file in files:
                try:
                    # porcelain.reset_file only accepts relative paths to the repo path
                    file_path = Path(file)
                    if file_path.is_absolute():
                        # index_file = file_path.relative_to(self.repo_path).as_posix()
                        index_file = str(file_path.relative_to(self.repo_path))
                    else:
                        index_file = file
                    git.reset_file(self.repo, index_file)
                except BaseException as e:
                    self.log('Error reset: {0}'.format(e))

    def reset(self):
        """Discard all the changes."""
        if self.repo:
            git.reset(self.repo, 'hard')

    def archive(self, branch: str, file: str) -> bool:
        """
        Archive a branch to a target file.

        Parameters
        ----------
        branch : str
            Name of the branch to archive
        file : str
            Output file.
        """
        if self.repo:
            try:
                with Path(file).open('wb') as f:
                    git.archive(self.repo, branch, f)
                return True
            except BaseException as e:
                self.log('Error archive: {0}'.format(e))
        return False

    def commit(self, commit_text: str):
        """
        Commit the changes.

        Parameters
        ----------
        commit_text : str
            Message associated to the commit.
        """
        if self.repo:
            git.commit(self.repo, message=commit_text)
