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

"""Front-end for Git commands."""

from abc import ABCMeta, abstractmethod
import configparser
from enum import Enum
import os
from pathlib import Path, PurePosixPath
import site
import sys
from typing import Dict, Iterator, List, Optional, Tuple, Union

# force user installed modules to have priority on Python installation
site_user = site.getusersitepackages()
if site_user in sys.path:
    sys.path.remove(site_user)
    sys.path.insert(1, site_user)

import dulwich as dulwich  # noqa: E402
from dulwich import porcelain as git  # noqa: E402
from dulwich.objects import Blob, Commit, Tag, Tree  # noqa: E402
from dulwich.objectspec import parse_commit  # noqa: E402
from dulwich.repo import Repo  # noqa: E402

# minimum Dulwich version
min_dulwich_ver = (0, 21, 3)
tree_mode = 0o040000
gitlink_mode = 0o160000
Committish = Union[str, bytes, Commit, Tag]

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
        # internal error
        'none',
    ],
)


def normalize_git_path(path: Union[str, bytes]) -> str:
    """Normalize Dulwich path values for stable key matching."""
    path_str = path.decode('utf-8') if isinstance(path, bytes) else path
    return path_str.replace('\\', '/').rstrip('/')


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

    return ''


class GitClient(metaclass=ABCMeta):
    """Provide access to Git commands."""

    def __init__(self):
        self.repo_path = ''
        self.repo_name = ''
        self.branch = ''
        self.repo = None
        self.files_status = {}
        self.submodules_paths = []
        # check Dulwich version
        dulwich_ver = dulwich.__version__
        if dulwich_ver < min_dulwich_ver:  # pyright: ignore[reportOperatorIssue]
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
        self.submodules_paths = []
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
            # typing annotation incorrect for git.status: str | Repo
            staged, unstaged, untracked = git.status(self.repo)  # type: ignore

            staged_add = {normalize_git_path(file) for file in staged['add']}
            staged_modify = {normalize_git_path(file) for file in staged['modify']}
            staged_delete = {normalize_git_path(file) for file in staged['delete']}
            unstaged_set = {normalize_git_path(file) for file in unstaged}
            untracked_list = [normalize_git_path(file) for file in untracked]

            # list files & status in git repo
            repo_files = [normalize_git_path(file) for file in git.ls_files(self.repo)]
            for file in repo_files:
                file_str = file
                # ['added', 'removed_staged', 'modified_staged', 'modified_unstaged',
                # 'untracked', 'removed_unstaged', 'clean', 'extern']
                if file_str in staged_add:
                    status = GitStatus.added
                # deleted staged files are not listed in ls_files
                # elif (file in staged['delete']):
                #    status = GitStatus.removed_staged
                elif file_str in staged_modify:
                    status = GitStatus.modified_staged
                elif file_str in unstaged_set:
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
            for file_str in staged_delete:
                status = GitStatus.removed_staged
                self.files_status[file_str] = status

            # untracked files are not listed in ls_files
            # untracked returned as str, Windows path in 19.13 but posix in 21.3
            for file_str in untracked_list:
                status = GitStatus.untracked
                self.files_status[file_str] = status

            # get submodules paths
            self.submodules_paths = self.get_submodule_paths()
            return True
        else:
            self.repo_name = ''
            self.branch = ''
            self.repo = None
            return False

    def _walk_commits(self, commit_id, commits_dict):
        """
        Depth-first traversal, avoiding duplicates.

        Returns
        -------
        Fill commits_dict with commit_id: timestamp pairs.
        """
        if self.repo:
            if commit_id in commits_dict:
                return
            try:
                obj = self.repo[commit_id]
                # Check if it's a Commit object
                if isinstance(obj, Commit):
                    commits_dict[commit_id] = obj.commit_time
                    for parent_id in obj.parents:
                        self._walk_commits(parent_id, commits_dict)
            except KeyError:
                pass  # Commit not found (edge case)

    def get_commits_list(self) -> List[Tuple]:
        """
        Return the list of the repository's commits.

        Parameters
        ----------
        Commit is a tuple (commit_id, timestamp).
        Commits are sorted by timestamp, newest first.

        Returns
        -------
        List[Tuple]
        """
        all_commits = {}  # Use dict
        if self.repo:
            # Walk all refs (branches, tags, etc.)
            for refname, refvalue in self.repo.refs.as_dict().items():
                if refvalue:
                    self._walk_commits(refvalue, all_commits)

        # Sort by timestamp (descending)
        all_commits_list = sorted(all_commits.items(), key=lambda x: x[1], reverse=True)
        # for testing
        # fill list until 1000 entries
        # for i in range(len(all_commits_list), 1000):
        #    all_commits_list.append(all_commits_list[-1])

        # return 1000 newest commits
        return all_commits_list[:1000]

    def get_branch_list(self) -> List[str]:
        """
        Return the list of the repository's branches.

        Returns
        -------
        List[str]
        """
        if self.repo:
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
                    # self.log("not status: %s %s" % (abspath, abspath.exists()))
                    if abspath.exists():
                        if self.is_submodule_file(abspath):
                            status = GitStatus.extern
                        else:
                            status = GitStatus.untracked
                    else:
                        status = GitStatus.error
                return index_file_name, status
            except ValueError:
                return file_path, GitStatus.extern
        else:
            return '', GitStatus.none

    def get_submodule_paths(self, committish: Optional[Committish] = None) -> List[str]:
        """Return the list of absolute submodule paths for a commit."""
        if not self.repo or not self.repo_path:
            return []

        try:
            commit = self._resolve_commit(self.repo, committish)
        except BaseException as e:
            self.log('Error submodules: {0}'.format(e))
            return []

        return [
            (Path(self.repo_path) / self._to_local_path(rel_path)).resolve()
            for rel_path, mode, _ in self._iter_tree(self.repo, commit.tree)
            if mode == gitlink_mode
        ]

    def is_submodule_file(self, path: Path) -> bool:
        """Return whether a path is a submodule or belongs to one."""
        normalized = os.path.normcase(str(path.resolve()))
        for submodule_path in self.submodules_paths:
            normalized_submodule = os.path.normcase(str(submodule_path))
            if normalized == normalized_submodule or normalized.startswith(
                normalized_submodule + os.sep
            ):
                return True
        return False

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
                # Dulwich resolves relative paths against the process working directory.
                repo_path = Path(self.repo_path)
                paths = [
                    str(file_path if file_path.is_absolute() else repo_path / file_path)
                    for file in files
                    for file_path in [Path(file)]
                ]
                return git.add(self.repo, paths)  # type: ignore
            except BaseException as e:
                self.log('Error stage: {0}'.format(e))

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

    def archive(self, committish: Optional[Committish], file: str) -> bool:
        """
        Archive a committish to a target file.

        Parameters
        ----------
        committish : str
            Name of the committish to archive
        file : str
            Output file.
        """
        if self.repo:
            try:
                with Path(file).open('wb') as f:
                    git.archive(self.repo, committish, f)
                return True
            except BaseException as e:
                self.log('Error archive: {0}'.format(e))
        return False

    def _resolve_commit(self, repo: Repo, committish: Optional[Committish]) -> Commit:
        """Resolve a commit-like reference into a Commit object."""
        if isinstance(committish, Commit):
            return committish

        if isinstance(committish, Tag):
            return parse_commit(repo, committish.object[1])

        if committish is None:
            return parse_commit(repo, b'HEAD')

        if isinstance(committish, str):
            return parse_commit(repo, committish.encode('utf-8'))

        return parse_commit(repo, committish)

    def _iter_tree(
        self, repo: Repo, tree_id: bytes, prefix: str = ''
    ) -> Iterator[Tuple[str, int, bytes]]:
        """Yield tree entries recursively as (path, mode, sha)."""
        tree: Tree = repo[tree_id]
        for name, mode, sha in tree.iteritems():
            name_str = name.decode('utf-8')
            path = ''.join([prefix, name_str])
            yield path, mode, sha
            if mode == tree_mode:
                yield from self._iter_tree(repo, sha, ''.join([path, '/']))

    def _to_local_path(self, rel_posix_path: str) -> Path:
        """Return a local path from a POSIX Git path."""
        return Path(*PurePosixPath(rel_posix_path).parts)

    def _safe_output_path(self, output_dir: Path, rel_posix_path: str) -> Path:
        """Build a path under output_dir and reject traversal."""
        out_file = (output_dir / self._to_local_path(rel_posix_path)).resolve()
        out_root = output_dir.resolve()
        if out_file != out_root and out_root not in out_file.parents:
            raise ValueError('Path traversal blocked: {0}'.format(rel_posix_path))
        return out_file

    def _read_blob_at_path(self, repo: Repo, tree_id: bytes, rel_posix_path: str) -> bytes:
        """Read a blob from a tree using a POSIX relative path."""
        tree: Tree = repo[tree_id]
        parts = [p.encode('utf-8') for p in PurePosixPath(rel_posix_path).parts]
        for i, part in enumerate(parts):
            found = False
            for name, mode, sha in tree.iteritems():
                if name == part:
                    found = True
                    last = i == len(parts) - 1
                    if last:
                        obj = repo[sha]
                        if isinstance(obj, Blob):
                            return obj.data
                        raise KeyError(rel_posix_path)
                    if mode != tree_mode:
                        raise KeyError(rel_posix_path)
                    tree = repo[sha]
                    break
            if not found:
                raise KeyError(rel_posix_path)
        raise KeyError(rel_posix_path)

    def _parse_gitmodules(self, gitmodules_data: bytes) -> Dict[str, str]:
        """Parse .gitmodules and return path -> url mapping."""
        parser = configparser.ConfigParser(interpolation=None)
        parser.read_string(gitmodules_data.decode('utf-8', errors='replace'))

        paths_to_urls = {}
        for section in parser.sections():
            path = parser.get(section, 'path', fallback='')
            url = parser.get(section, 'url', fallback='')
            if path and url:
                paths_to_urls[path] = url
        return paths_to_urls

    def _export_commit_files(self, repo: Repo, commit: Commit, output_dir: Path):
        """Export regular files of a commit tree to output_dir."""
        for rel_path, mode, sha in self._iter_tree(repo, commit.tree):
            if mode == tree_mode or mode == gitlink_mode:
                continue

            obj = repo[sha]
            if not isinstance(obj, Blob):
                continue

            out_file = self._safe_output_path(output_dir, rel_path)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_bytes(obj.data)

    def _export_with_submodules(
        self,
        repo: Repo,
        repo_dir: Path,
        commit: Commit,
        output_dir: Path,
    ) -> bool:
        """Export commit files and recurse into local submodules."""
        self._export_commit_files(repo, commit, output_dir)

        try:
            gitmodules = self._read_blob_at_path(repo, commit.tree, '.gitmodules')
            submodule_urls = self._parse_gitmodules(gitmodules)
        except KeyError:
            submodule_urls = {}

        for rel_path, mode, sha in self._iter_tree(repo, commit.tree):
            if mode != gitlink_mode:
                continue

            submodule_repo_path = repo_dir / self._to_local_path(rel_path)
            submodule_output_dir = output_dir / self._to_local_path(rel_path)
            submodule_output_dir.mkdir(parents=True, exist_ok=True)

            try:
                submodule_repo = Repo(str(submodule_repo_path))
            except BaseException:
                if rel_path in submodule_urls:
                    self.log(
                        'Error export: submodule not found locally at {0} (url: {1})'.format(
                            submodule_repo_path, submodule_urls[rel_path]
                        )
                    )
                else:
                    self.log(
                        'Error export: submodule not found locally at {0}'.format(
                            submodule_repo_path
                        )
                    )
                return False

            try:
                submodule_commit = self._resolve_commit(submodule_repo, sha)
            except BaseException as e:
                self.log(
                    'Error export: cannot resolve submodule commit for {0}: {1}'.format(rel_path, e)
                )
                return False

            if not self._export_with_submodules(
                submodule_repo,
                submodule_repo_path,
                submodule_commit,
                submodule_output_dir,
            ):
                return False

        return True

    def export_to_directory(self, committish: Optional[Committish], output_dir: str) -> bool:
        """
        Export a version to a plain directory, including submodules.

        The output directory is a plain file copy (no .git metadata).

        Parameters
        ----------
        committish : str | bytes | Commit | Tag | None
            Name or id of the committish to export.
        output_dir : str
            Target output directory. It must be empty or not exist.
        """
        if not self.repo or not self.repo_path:
            return False

        try:
            output_path = Path(output_dir)
            if output_path.exists() and any(output_path.iterdir()):
                raise ValueError('Output directory is not empty: {0}'.format(output_path))
            output_path.mkdir(parents=True, exist_ok=True)

            commit = self._resolve_commit(self.repo, committish)
            return self._export_with_submodules(
                self.repo,
                Path(self.repo_path),
                commit,
                output_path,
            )
        except BaseException as e:
            self.log('Error export: {0}'.format(e))
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
            # typing annotation incorrect for git.commit: str | Repo
            git.commit(self.repo, message=commit_text)  # type: ignore
