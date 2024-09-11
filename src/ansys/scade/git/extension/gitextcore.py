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

"""SCADE custom extension for Git."""

from inspect import getsourcefile
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
from typing import Union

import scade
from scade.model.project.stdproject import FileRef, Project

from ansys.scade.git.extension.gitclient import GitClient, GitStatus
from ansys.scade.git.extension.ide import Command, Ide

# configuration parameters
BrowserCat = {
    'Staged': 'Staged files',
    'Unstaged': 'Unstaged files',
    'Clean': 'Clean files',
    'Extern': 'Extern files',
}


def create_temp_dir(folder: str):
    """
    Create a temporary directory.

    If the folder already exists, it is deleted.

    Parameters
    ----------
    text : str
        Message to display.
    """
    tmp_dir = Path(tempfile.gettempdir()) / folder
    shutil.rmtree(tmp_dir, ignore_errors=True)
    tmp_dir.mkdir(parents=True)
    return tmp_dir


def create_browser(ide: Ide, branch_name: str):
    """
    Create a 'Git' browser in the IDE.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    branch_name : str
        Name of the browser.
    """
    ide.create_browser('Git', icons["git"])
    ide.browser_report(branch_name, None, True)
    ide.browser_report(BrowserCat['Staged'], branch_name, True)
    ide.browser_report(BrowserCat['Unstaged'], branch_name, True)
    ide.browser_report(BrowserCat['Clean'], branch_name, False)
    ide.browser_report(BrowserCat['Extern'], branch_name, False)


def report_item(ide: Ide, item: Union[Project, FileRef, str]) -> str:
    """
    Add an item to the Git browser and return its path.

    The item is attached to one of the predefined categories with respect to
    its status. It can be

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    item: Union[Project, FileRef, str]
        Element to add to the browser: Either a SCADE Python object or a string.
    """
    if isinstance(item, str):
        index_file_name, status = _git_client.get_file_status(item)
        browser_cat, icon = status_data.get(status, GitStatus.extern)
        project_files_status[browser_cat].append(index_file_name)
        ide.browser_report(index_file_name, browser_cat, icon_file=icon)
    else:
        index_file_name, status = _git_client.get_file_status(item.pathname)
        browser_cat, icon = status_data.get(status, GitStatus.extern)
        project_files_status[browser_cat].append(index_file_name)
        if isinstance(item, Project):
            name = index_file_name
        else:
            name = item.persist_as if Path(index_file_name).is_absolute() else index_file_name
        ide.browser_report(item, browser_cat, icon_file=icon, name=name)
    return index_file_name


def refresh_browser(ide: Ide):
    """
    Refresh the Git browser.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """
    active_project = ide.get_active_project()
    if active_project:
        # save project before Git refresh
        # active_project.save(active_project.pathname) # crash the editor on reload
        if _git_client.refresh(active_project.pathname):
            ide.log('Refreshed git repo {0}'.format(_git_client.repo_path))
            branch_name = 'branch: ' + _git_client.branch

            # create SCADE Git browser
            create_browser(ide, branch_name)

            # clear files status lists
            project_files_status[BrowserCat['Staged']].clear()
            project_files_status[BrowserCat['Unstaged']].clear()
            project_files_status[BrowserCat['Clean']].clear()
            project_files_status[BrowserCat['Extern']].clear()

            # look for files present in the SCADE project
            project_files = []
            for project in ide.get_projects():
                # for project file
                project_files.append(report_item(ide, project))
                # for files registered in the project
                for fr in project.file_refs:
                    project_files.append(report_item(ide, fr))
                    # check if ann file for xscade
                    filepath = Path(fr.pathname)
                    if filepath.suffix == '.xscade':
                        ann_file = filepath.with_suffix('.ann')
                        if ann_file.exists():
                            project_files.append(report_item(ide, str(ann_file)))

            # look for files in git but not in the project: deleted files
            # not possible as the repo can contain several SCADE projects

            return
            # todo: symbol file has no absolute path, relative to the project ?
            for session in scade.model.suite.get_roots():
                # symbols files
                model = session.model
                for subop in model.sub_operators:
                    symbol_file = subop.symbol_file
                    ide.log('file: {0}'.format(str(symbol_file)))
                    if str(symbol_file) != '':
                        ide.log('file 2: {0}'.format(str(symbol_file)))
        else:
            ide.log("No repository found")
    else:
        ide.log("No project loaded")


class CmdRefresh(Command):
    """
    SCADE Command: Refresh.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Refresh',
            status_message='Refresh the Git repo status',
            tooltip_message='Refresh the Git repo status',
            image_file=res['refresh'],
        )

    def on_activate(self):
        """Run the command."""
        refresh_browser(self.ide)


class GitRepoCommand(Command):
    """Base class for commands that require a valid Git repository."""

    def on_enable(self) -> bool:
        """Enable the command if the Git repository exists and is refreshed."""
        return _git_client.repo is not None


class CmdStage(GitRepoCommand):
    """
    SCADE Command: Stage.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Stage',
            status_message='Stage selected files',
            tooltip_message='Stage selected files',
            image_file=res['stage'],
        )

    def on_activate(self):
        """Run the command."""
        files_to_process = list()
        for item in self.ide.selection:
            if isinstance(item, FileRef) or isinstance(item, Project):
                files_to_process.append(item.pathname)
        if files_to_process:
            _git_client.stage(files_to_process)
            refresh_browser(self.ide)


class CmdUnstage(GitRepoCommand):
    """
    SCADE Command: Unstage.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Unstage',
            status_message='UnStage selected files',
            tooltip_message='UnStage selected files',
            image_file=res['unstage'],
        )

    def on_activate(self):
        """Run the command."""
        files_to_process = list()
        for item in self.ide.selection:
            if isinstance(item, FileRef) or isinstance(item, Project):
                files_to_process.append(item.pathname)
        if files_to_process:
            _git_client.unstage(files_to_process)
            refresh_browser(self.ide)


class CmdReset(GitRepoCommand):
    """
    SCADE Command: Reset.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Reset',
            status_message='Reset selected files',
            tooltip_message='Reset selected files',
            image_file=res['reset'],
        )

    def on_activate(self):
        """Run the command."""
        files_to_process = list()
        for item in self.ide.selection:
            if isinstance(item, FileRef) or isinstance(item, Project):
                files_to_process.append(item.pathname)
        if files_to_process:
            _git_client.reset_files(files_to_process)
            refresh_browser(self.ide)


class CmdStageAll(GitRepoCommand):
    """
    SCADE Command: Stage All.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Stage All',
            status_message='Stage all files',
            tooltip_message='Stage all files',
            image_file=res['stage'],
        )

    def on_activate(self):
        """Run the command."""
        refresh_browser(self.ide)
        _git_client.stage(project_files_status[BrowserCat['Unstaged']])
        refresh_browser(self.ide)


class CmdUnstageAll(GitRepoCommand):
    """
    SCADE Command: Unstage All.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Unstage All',
            status_message='Unstage all files',
            tooltip_message='Unstage all files',
            image_file=res['unstage'],
        )

    def on_activate(self):
        """Run the command."""
        refresh_browser(self.ide)
        _git_client.unstage(project_files_status[BrowserCat['Staged']])
        refresh_browser(self.ide)


class CmdResetAll(GitRepoCommand):
    """
    SCADE Command: Reset All.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Reset All',
            status_message='Reset all files',
            tooltip_message='Reset all files',
            image_file=res['reset'],
        )

    def on_activate(self):
        """Run the command."""
        confirm = self.confirm_reset()
        if confirm:
            _git_client.reset()
            refresh_browser(self.ide)

    def confirm_reset(self) -> bool:
        """Provide a default behavior for command line tools."""
        return True


class CmdCommit(GitRepoCommand):
    """
    SCADE Command: Commit.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Commit',
            status_message='Commit',
            tooltip_message='Commit',
            image_file=res['commit'],
        )

    def on_activate(self):
        """Run the command."""
        refresh_browser(self.ide)
        if project_files_status[BrowserCat['Unstaged']]:
            confirm = self.confirm_commit()
            if not confirm:
                return

        commit_text = self.get_commit_text()
        if commit_text:
            _git_client.commit(commit_text)
            refresh_browser(self.ide)

    def confirm_commit(self) -> bool:
        """Provide a default behavior for command line tools."""
        return True

    def get_commit_text(self) -> str:
        """Provide a default behavior for command line tools."""
        return 'some message'


class CmdDiff(GitRepoCommand):
    """
    SCADE Command: Diff.

    Parameters
    ----------
    ide : Studio
        SCADE IDE environment.
    """

    def __init__(self, ide: Ide):
        super().__init__(
            ide,
            name='Diff',
            status_message='Diff project with another version',
            tooltip_message='Diff project with another version',
            image_file=res['diff'],
        )

    def on_activate(self):
        """Run the command."""
        branch = self.select_branch()
        if branch:
            branch_path = "".join([c for c in branch if c.isalnum() or c in "._-"])
            tmp_dir = create_temp_dir(
                os.path.join('SCADE', 'git-diff', _git_client.repo_name, branch_path)
            )
            active_project = self.ide.get_projects()[0]
            diff_project = tmp_dir / Path(active_project.pathname).relative_to(
                _git_client.repo_path
            )
            # create a tar archive of the branch
            archive_file = tmp_dir.with_suffix('.tar')
            _git_client.archive(branch, archive_file)
            if archive_file.exists():
                # untar the archive in tmp_dir
                tar_file = tarfile.open(archive_file)
                tar_file.extractall(tmp_dir)
                tar_file.close()
                # delete the tar archive"
                archive_file.unlink()
                # display the branch project to compare with the current
                # project in the Git output tab
                if diff_project.exists():
                    self.ide.log(
                        'Launch the Diff Analyzer tool with the project\n   {0}'.format(
                            str(diff_project)
                        )
                    )
                    # self.ide.log('module scade: {0}'.format(getmembers(scade.tool.suite.diff)))
                    # scade.tool.suite.diff_analyze(active_project.pathname, diff_project.asposix())

    def select_branch(self) -> str:
        """Provide a default behavior for command line tools."""
        return 'main'


script_path = Path(os.path.abspath(getsourcefile(lambda: 0)))
script_dir = script_path.parent

res = {
    "refresh": str(script_dir / 'img/refresh.bmp'),
    "stage": str(script_dir / 'img/stage.bmp'),
    "unstage": str(script_dir / 'img/unstage.bmp'),
    "reset": str(script_dir / 'img/unstage.bmp'),
    "commit": str(script_dir / 'img/commit.bmp'),
    "diff": str(script_dir / 'img/diff.bmp'),
}

icons = {
    "git": str(script_dir / 'img/git.ico'),
}

# status_data: browser category, icon
status_data = {
    GitStatus.added: [BrowserCat['Staged'], str(script_dir / 'img/added.ico')],
    GitStatus.removed_staged: [BrowserCat['Staged'], str(script_dir / 'img/removed.ico')],
    GitStatus.modified_staged: [BrowserCat['Staged'], str(script_dir / 'img/modified.ico')],
    GitStatus.removed_unstaged: [BrowserCat['Unstaged'], str(script_dir / 'img/removed.ico')],
    GitStatus.modified_unstaged: [BrowserCat['Unstaged'], str(script_dir / 'img/modified.ico')],
    GitStatus.untracked: [BrowserCat['Unstaged'], str(script_dir / 'img/untracked.ico')],
    GitStatus.clean: [BrowserCat['Clean'], str(script_dir / 'img/clean.ico')],
    GitStatus.extern: [BrowserCat['Extern'], str(script_dir / 'img/extern.ico')],
    GitStatus.error: [BrowserCat['Extern'], str(script_dir / 'img/error.ico')],
}

project_files_status = {
    BrowserCat['Staged']: [],
    BrowserCat['Unstaged']: [],
    BrowserCat['Clean']: [],
    BrowserCat['Extern']: [],
}

_git_client = None


def set_git_client(git_client: GitClient):
    """
    Set the global variable _git_client.

    Parameters
    ----------
    git_client : GitClient
        Instance of GitClient.
    """
    global _git_client
    _git_client = git_client
