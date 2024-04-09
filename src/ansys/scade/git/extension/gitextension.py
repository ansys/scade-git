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

# from scade.tool.suite.gui import register_load_model_callable, register_unload_model_callable
import scade
from scade.model.project.stdproject import FileRef, Project, get_roots as get_projects
from scade.tool.suite.gui.commands import Command, ContextMenu, Menu, Toolbar
from scade.tool.suite.gui.dialogs import Dialog, message_box
from scade.tool.suite.gui.widgets import Button, EditBox, ListBox

from ansys.scade.git.extension.gitclient import GitClient, GitStatus

# configuration parameters
BrowserCat = {'Staged': 'Staged files', 'Unstaged': 'Unstaged files', 'Clean': 'Clean files', 'Extern': 'Extern files'}


def log(text: str):
    """
    Display the input message in the `Messages` output tab.

    The messages are prefixed by 'Git Extension - '.

    Parameters
    ----------
    text : str
        Message to display.
    """
    if text:
        scade.tabput("LOG", "Git Extension - " + text + "\n")


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


def create_browser(branch_name: str):
    """
    Create a 'Git' browser in the IDE.

    Parameters
    ----------
    branch_name : str
        Name of the browser.
    """
    scade.create_browser('Git', icons["git"])
    scade.browser_report(branch_name, None, True)
    scade.browser_report(BrowserCat['Staged'], branch_name, True)
    scade.browser_report(BrowserCat['Unstaged'], branch_name, True)
    scade.browser_report(BrowserCat['Clean'], branch_name, False)
    scade.browser_report(BrowserCat['Extern'], branch_name, False)


def report_item(item: Union[Project, FileRef, str]) -> str:
    """
    Add an item to the Git browser and return its path.

    The item is attached to one of the predefined categories with respect to
    its status. It can be

    Parameters
    ----------
    item: Union[Project, FileRef, str]
        Element to add to the browser: Either a SCADE Python object or a string.
    """
    if isinstance(item, str):
        index_file_name, status = git_client.get_file_status(item)
        browser_cat, icon = status_data.get(status, GitStatus.extern)
        project_files_status[browser_cat].append(index_file_name)
        scade.browser_report(index_file_name, browser_cat, icon_file=icon)
    else:
        index_file_name, status = git_client.get_file_status(item.pathname)
        browser_cat, icon = status_data.get(status, GitStatus.extern)
        project_files_status[browser_cat].append(index_file_name)
        scade.browser_report(item, browser_cat, icon_file=icon, name=index_file_name)
    return index_file_name


class SelectBranchDialog(Dialog):
    """Custom dialog for selecting a branch."""
    def __init__(self, name):
        super().__init__(name, 300, 200)
        self.branch = None

    def on_build(self):
        """Build the dialog."""
        Button(self, 'Diff', 220, 15, 45, 25, self.on_close_click)
        Button(self, 'Cancel', 220, 55, 45, 25, self.on_cancel_click)
        branches = git_client.get_branch_list()
        ListBox(self, branches, 15, 15, 200, 100, self.on_list_branch_selection, style=['sort'])

    def on_close_click(self, button):
        """Close the dialog."""
        self.close()

    def on_cancel_click(self, button):
        """"Cancel the dialog."""
        self.branch = None
        self.close()

    def on_list_branch_selection(self, list, index):
        """"Store the selected branch."""
        branch = list.get_selection()
        if len(branch) == 1:
            self.branch = str(branch[0])
        else:
            log('Error: select only one branch: {0}'.format(branch))


class CommitDialog(Dialog):
    """Custom dialog for providing the commit message."""
    def __init__(self, name):
        super().__init__(name, 600, 200)
        self.commit_text = None

    def on_build(self):
        """Build the dialog."""
        Button(self, 'Commit', 520, 15, 45, 25, self.on_close_click)
        Button(self, 'Cancel', 520, 55, 45, 25, self.on_cancel_click)
        self.editbox = EditBox(self, 15, 15, 500, 100, style=['multiline'])

    def on_close_click(self, button):
        """Close the dialog if the message is not empty."""
        if self.editbox:
            commit_text = self.editbox.get_name().strip()
            if commit_text != '':
                self.commit_text = commit_text
                self.close()
            else:
                log('Error: commit text cannot be empty')

    def on_cancel_click(self, button):
        """"Cancel the dialog."""
        self.close()


class CmdRefresh(Command):
    """SCADE Command: Refresh."""
    def __init__(self):
        super().__init__(
            name='Refresh',
            status_message='Refresh the Git repo status',
            tooltip_message='Refresh the Git repo status',
            image_file=res['refresh'],
        )

    def on_activate(self):
        """Run the command."""
        active_project = scade.get_active_project()
        if active_project:
            # save project before Git refresh
            # active_project.save(active_project.pathname) # crash the editor on reload
            if git_client.refresh(active_project.pathname):
                log('Refreshed git repo {0}'.format(git_client.repo_path))
                branch_name = 'branch: ' + git_client.branch

                # create SCADE Git browser
                create_browser(branch_name)

                # clear files status lists
                project_files_status[BrowserCat['Staged']].clear()
                project_files_status[BrowserCat['Unstaged']].clear()
                project_files_status[BrowserCat['Clean']].clear()
                project_files_status[BrowserCat['Extern']].clear()

                # look for files present in the SCADE project
                project_files = []
                for project in get_projects():
                    # for project file
                    project_files.append(report_item(project))
                    # for files registered in the project
                    for fr in project.file_refs:
                        project_files.append(report_item(fr))
                        # check if ann file for xscade
                        filepath = Path(fr.pathname)
                        if filepath.suffix == '.xscade':
                            ann_file = filepath.with_suffix('.ann')
                            if ann_file.exists():
                                project_files.append(report_item(str(ann_file)))

                # look for files in git but not in the project: deleted files
                # not possible as the repo can contain several SCADE projects

                return
                # todo: symbol file has no absolute path, relative to the project ?
                for session in scade.model.suite.get_roots():
                    # symbols files
                    model = session.model
                    for subop in model.sub_operators:
                        symbol_file = subop.symbol_file
                        log('file: {0}'.format(str(symbol_file)))
                        if str(symbol_file) != '':
                            log('file 2: {0}'.format(str(symbol_file)))
            else:
                log("No repository found")
        else:
            log("No project loaded")


class GitRepoCommand(Command):
    """Base class for commands that require a valid Git repository."""
    def on_enable(self) -> bool:
        """Enable the command if the Git repository exists and is refreshed."""
        return git_client.repo is not None


class CmdStage(GitRepoCommand):
    """SCADE Command: Stage."""
    def __init__(self):
        super().__init__(
            name='Stage',
            status_message='Stage selected files',
            tooltip_message='Stage selected files',
            image_file=res['stage'],
        )

    def on_activate(self):
        """Run the command."""
        files_to_process = list()
        for item in scade.selection:
            if isinstance(item, FileRef) or isinstance(item, Project):
                files_to_process.append(item.pathname)
        if files_to_process:
            git_client.stage(files_to_process)
            cmd_refresh.on_activate()


class CmdUnstage(GitRepoCommand):
    """SCADE Command: Unstage."""
    def __init__(self):
        super().__init__(
            name='Unstage',
            status_message='UnStage selected files',
            tooltip_message='UnStage selected files',
            image_file=res['unstage'],
        )

    def on_activate(self):
        """Run the command."""
        files_to_process = list()
        for item in scade.selection:
            if isinstance(item, FileRef) or isinstance(item, Project):
                files_to_process.append(item.pathname)
        if files_to_process:
            git_client.unstage(files_to_process)
            cmd_refresh.on_activate()


class CmdReset(GitRepoCommand):
    """SCADE Command: Reset."""
    def __init__(self):
        super().__init__(
            name='Reset',
            status_message='Reset selected files',
            tooltip_message='Reset selected files',
            image_file=res['reset'],
        )

    def on_activate(self):
        """Run the command."""
        files_to_process = list()
        for item in scade.selection:
            if isinstance(item, FileRef) or isinstance(item, Project):
                files_to_process.append(item.pathname)
        if files_to_process:
            git_client.reset_files(files_to_process)
            cmd_refresh.on_activate()


class CmdStageAll(GitRepoCommand):
    """SCADE Command: Stage All."""
    def __init__(self):
        super().__init__(
            name='Stage All',
            status_message='Stage all files',
            tooltip_message='Stage all files',
            image_file=res['stage'],
        )

    def on_activate(self):
        """Run the command."""
        cmd_refresh.on_activate()
        git_client.stage(project_files_status[BrowserCat['Unstaged']])
        cmd_refresh.on_activate()


class CmdUnstageAll(GitRepoCommand):
    """SCADE Command: Unstage All."""
    def __init__(self):
        super().__init__(
            name='Unstage All',
            status_message='Unstage all files',
            tooltip_message='Unstage all files',
            image_file=res['unstage'],
        )

    def on_activate(self):
        """Run the command."""
        cmd_refresh.on_activate()
        git_client.unstage(project_files_status[BrowserCat['Staged']])
        cmd_refresh.on_activate()


class CmdResetAll(GitRepoCommand):
    """SCADE Command: Reset All."""
    def __init__(self):
        super().__init__(
            name='Reset All',
            status_message='Reset all files',
            tooltip_message='Reset all files',
            image_file=res['reset'],
        )

    def on_activate(self):
        """Run the command."""
        confirm = message_box(
            'Confirm Reset', 'Do you really want to reset the Git repo?', style='yesno', icon='warning'
        )
        if confirm == 6:
            git_client.reset()
            cmd_refresh.on_activate()


class CmdCommit(GitRepoCommand):
    """SCADE Command: Commit."""
    def __init__(self):
        super().__init__(name='Commit', status_message='Commit', tooltip_message='Commit', image_file=res['commit'])

    def on_activate(self):
        """Run the command."""
        cmd_refresh.on_activate()
        if project_files_status[BrowserCat['Unstaged']]:
            confirm = message_box(
                'Confirm Partial Commit',
                'There are unstagged files. Do you really want to do a partial commit?',
                style='yesno',
                icon='warning',
            )
            if confirm != 6:
                return
        commit_dialog = CommitDialog('Commit')
        commit_dialog.do_modal()
        if commit_dialog.commit_text:
            git_client.commit(commit_dialog.commit_text)
            cmd_refresh.on_activate()


class CmdDiff(GitRepoCommand):
    """SCADE Command: Diff."""
    def __init__(self):
        super().__init__(
            name='Diff',
            status_message='Diff project with another version',
            tooltip_message='Diff project with another version',
            image_file=res['diff'],
        )

    def on_activate(self):
        """Run the command."""
        select_branch = SelectBranchDialog('Select Branch')
        select_branch.do_modal()
        if select_branch.branch:
            branch_path = "".join([c for c in select_branch.branch if c.isalnum() or c in "._-"])
            tmp_dir = create_temp_dir(os.path.join('SCADE', 'git-diff', git_client.repo_name, branch_path))
            active_project = get_projects()[0]
            diff_project = tmp_dir / Path(active_project.pathname).relative_to(git_client.repo_path)
            # create a tar archive of the branch
            archive_file = tmp_dir.with_suffix('.tar')
            file = archive_file.open('w+b')
            git_client.archive(select_branch.branch, file)
            file.close()
            if archive_file.exists():
                # untar the archive in tmp_dir
                tar_file = tarfile.open(archive_file)
                tar_file.extractall(tmp_dir)
                tar_file.close()
                # delete the tar archive"
                archive_file.unlink()
                # display the branch project to compare with the current project in the Git output tab
                if diff_project.exists():
                    log('Launch the Diff Analyzer tool with the project\n   {0}'.format(str(diff_project)))
                    # log('module scade: {0}'.format(getmembers(scade.tool.suite.diff)))
                    # scade.tool.suite.diff_analyze(active_project.pathname, diff_project.asposix())


# def on_load_model(project):
#     log('load model')


# def on_unload_model(project):
#     log('unload model')


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
    GitStatus.extern: [BrowserCat['Extern'], str(script_dir / 'img/error.ico')],
}

project_files_status = {
    BrowserCat['Staged']: [],
    BrowserCat['Unstaged']: [],
    BrowserCat['Clean']: [],
    BrowserCat['Extern']: [],
}

git_client = GitClient(log)

if git_client.get_init_status():
    log('Loaded extension')
    cmd_refresh = CmdRefresh()
    cmd_stage = CmdStage()
    cmd_unstage = CmdUnstage()
    cmd_reset = CmdReset()
    cmd_stage_all = CmdStageAll()
    cmd_unstage_all = CmdUnstageAll()
    cmd_reset_all = CmdResetAll()
    cmd_commit = CmdCommit()
    cmd_diff = CmdDiff()

    Menu([cmd_refresh, cmd_stage_all, cmd_unstage_all, cmd_commit, cmd_diff], '&Project/Git')
    Toolbar('Git', [cmd_refresh, cmd_stage_all, cmd_unstage_all, cmd_commit, cmd_diff])
    ContextMenu([cmd_stage, cmd_unstage], lambda context: context == 'SCRIPT')

    # register_load_model_callable(on_load_model)
    # register_unload_model_callable(on_unload_model)
else:
    log('Git client not initialized')
