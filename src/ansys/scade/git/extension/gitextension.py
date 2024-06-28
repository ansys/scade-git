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

from typing import Any, List

# from scade.tool.suite.gui import register_load_model_callable, register_unload_model_callable
import scade
from scade.model.project.stdproject import Project, get_roots as get_projects
from scade.tool.suite.gui.commands import ContextMenu, Menu, Toolbar
from scade.tool.suite.gui.dialogs import Dialog, message_box
from scade.tool.suite.gui.widgets import Button, EditBox, ListBox

from ansys.scade.git.extension.gitclient import GitClient as AbsGitClient
from ansys.scade.git.extension.gitextcore import (
    CmdCommit as CoreCmdCommit,
    CmdDiff as CoreCmdDiff,
    CmdRefresh,
    CmdReset,
    CmdResetAll as CoreCmdResetAll,
    CmdStage,
    CmdStageAll,
    CmdUnstage,
    CmdUnstageAll,
    set_git_client,
)
from ansys.scade.git.extension.ide import Ide


class Studio(Ide):
    """Provide an implementation for SCADE IDE."""

    def create_browser(self, name: str, icon: str = None):
        """Redirect the call to SCADE IDE."""
        scade.create_browser(name, icon)

    def browser_report(
        self,
        item: Any,
        parent: Any = None,
        expanded: bool = False,
        name: str = '',
        icon_file: str = '',
    ):
        """Redirect the call to SCADE IDE."""
        if icon_file:
            scade.browser_report(item, parent, expanded=expanded, name=name, icon_file=icon_file)
        else:
            scade.browser_report(item, parent, expanded=expanded, name=name)

    @property
    def selection(self) -> List[Any]:
        """Redirect the call to SCADE IDE."""
        return scade.selection

    def get_active_project(self) -> Project:
        """Redirect the call to SCADE IDE."""
        return scade.get_active_project()

    def get_projects(self) -> List[Any]:
        """Redirect the call to the API."""
        return get_projects()

    def log(self, text: str):
        """Redirect the call to the locall log function."""
        log(text)


class GitClient(AbsGitClient):
    """GitClient implementation to log the messages to the IDE."""

    def log(self, text: str):
        """Print the logs to the SCADE Message output tab."""
        log(text)


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
        """Cancel the dialog."""
        self.branch = None
        self.close()

    def on_list_branch_selection(self, list, index):
        """Store the selected branch."""
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
        """Cancel the dialog."""
        self.close()


class CmdResetAll(CoreCmdResetAll):
    """SCADE Command: Reset All."""

    def confirm_reset(self) -> bool:
        """Override default behavior."""
        confirm = message_box(
            'Confirm Reset',
            'Do you really want to reset the Git repo?',
            style='yesno',
            icon='warning',
        )
        return confirm == 6


class CmdCommit(CoreCmdCommit):
    """SCADE Command: Commit."""

    def confirm_commit(self) -> bool:
        """Override default behavior."""
        confirm = message_box(
            'Confirm Partial Commit',
            'There are unstagged files. Do you really want to do a partial commit?',
            style='yesno',
            icon='warning',
        )
        return confirm == 6

    def get_commit_text(self) -> str:
        """Override default behavior."""
        commit_dialog = CommitDialog('Commit')
        commit_dialog.do_modal()
        return commit_dialog.commit_text


class CmdDiff(CoreCmdDiff):
    """SCADE Command: Diff."""

    def select_branch(self) -> str:
        """Override default behavior."""
        select_branch = SelectBranchDialog('Select Branch')
        select_branch.do_modal()
        return select_branch.branch


# def on_load_model(project):
#     log('load model')


# def on_unload_model(project):
#     log('unload model')


git_client = GitClient()
set_git_client(git_client)

if git_client.get_init_status():
    log('Loaded Git extension')
    studio = Studio()
    cmd_refresh = CmdRefresh(studio)
    cmd_stage = CmdStage(studio)
    cmd_unstage = CmdUnstage(studio)
    cmd_reset = CmdReset(studio)
    cmd_stage_all = CmdStageAll(studio)
    cmd_unstage_all = CmdUnstageAll(studio)
    cmd_reset_all = CmdResetAll(studio)
    cmd_commit = CmdCommit(studio)
    cmd_diff = CmdDiff(studio)

    Menu([cmd_refresh, cmd_stage_all, cmd_unstage_all, cmd_commit, cmd_diff], '&Project/Git')
    Toolbar('Git', [cmd_refresh, cmd_stage_all, cmd_unstage_all, cmd_commit, cmd_diff])
    ContextMenu([cmd_stage, cmd_unstage], lambda context: context == 'SCRIPT')

    # register_load_model_callable(on_load_model)
    # register_unload_model_callable(on_unload_model)
else:
    log('Git client not initialized')
