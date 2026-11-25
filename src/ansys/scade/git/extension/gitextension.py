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

"""SCADE custom extension for Git."""

# from scade.tool.suite.gui import register_load_model_callable, register_unload_model_callable
from typing import List, Tuple

import scade
from scade.tool.suite.gui.commands import ContextMenu, Menu, Toolbar
from scade.tool.suite.gui.dialogs import Dialog, message_box
from scade.tool.suite.gui.widgets import Button, EditBox, ListBox

from ansys.scade.git.extension.gitclient import GitClient as AbsGitClient
from ansys.scade.git.extension.gitextcore import (
    CmdCommit as CoreCmdCommit,
    CmdDiff as CoreCmdDiff,
    CmdRefresh,
    CmdReset,
    CmdStage,
    CmdStageAll,
    CmdUnstage,
    CmdUnstageAll,
    set_git_client,
)
from ansys.scade.guitools.studio import studio

# add debugging support for the extension
#import ansys.scade.git.extension.debug_vsc


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
        # scade is a CPython module defined dynamically
        scade.tabput("LOG", "Git Extension - " + text + "\n")  # type: ignore


class SelectVersionDialog(Dialog):
    """Custom dialog for selecting a branch or commit."""

    def __init__(self, name: str, versions: List[Tuple[str, List[str]]]):
        super().__init__(name, 440, 240)
        self.versions = versions
        self.items = []
        self.indices = []
        for type_index, (version_type, entries) in enumerate(versions):
            for entry_index, entry in enumerate(entries):
                self.items.append(f'{version_type}: {entry} [{entry_index + 1}]')
                self.indices.append([type_index, entry_index])
        self.pending_selection = [-1, -1]
        self.selection = [-1, -1]

    def on_build(self):
        """Build the dialog."""
        Button(self, 'Diff', 380, 15, 45, 25, self.on_close_click)
        Button(self, 'Cancel', 380, 55, 45, 25, self.on_cancel_click)
        ListBox(self, self.items, 15, 15, 350, 190, self.on_list_version_selection)

    def on_close_click(self, button):
        """Confirm the selected version."""
        if self.pending_selection == [-1, -1]:
            log('Error: select one version to diff')
        else:
            self.selection = self.pending_selection
            self.close()

    def on_cancel_click(self, button):
        """Cancel without selecting a version."""
        self.close()

    def on_list_version_selection(self, list, index):
        """Store the currently highlighted version."""
        selected = list.get_selection()
        if len(selected) == 1 and selected[0] in self.items:
            self.pending_selection = self.indices[self.items.index(selected[0])]
        else:
            self.pending_selection = [-1, -1]


class CommitDialog(Dialog):
    """Custom dialog for providing the commit message."""

    def __init__(self, name):
        super().__init__(name, 600, 200)
        self.commit_text = ''

    def on_build(self):
        """Build the dialog."""
        Button(self, 'Commit', 520, 15, 45, 25, self.on_close_click)
        Button(self, 'Cancel', 520, 55, 45, 25, self.on_cancel_click)
        self.editbox = EditBox(self, 15, 15, 500, 100, style=['multiline'])

    def on_close_click(self, button):
        """Close the dialog if the message is not empty."""
        if self.editbox:
            # Edit.get_name(): wrong typing annotation
            value: str = self.editbox.get_name()  # type: ignore
            commit_text = value.strip()
            if commit_text != '':
                self.commit_text = commit_text
                self.close()
            else:
                log('Error: commit text cannot be empty')

    def on_cancel_click(self, button):
        """Cancel the dialog."""
        self.close()


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

    def select_diff_version(self) -> List[int]:
        """Override default behavior."""
        dialog = SelectVersionDialog('Select Version', self.versions)
        dialog.do_modal()
        return dialog.selection


# def on_load_model(project):
#     log('load model')


# def on_unload_model(project):
#     log('unload model')


git_client = GitClient()
set_git_client(git_client)

if git_client.get_init_status():
    log('Loaded Git extension')
    cmd_refresh = CmdRefresh(studio)
    cmd_stage = CmdStage(studio)
    cmd_unstage = CmdUnstage(studio)
    cmd_reset = CmdReset(studio)
    cmd_stage_all = CmdStageAll(studio)
    cmd_unstage_all = CmdUnstageAll(studio)
    cmd_commit = CmdCommit(studio)
    cmd_diff = CmdDiff(studio)

    Menu([cmd_refresh, cmd_stage_all, cmd_unstage_all, cmd_commit, cmd_diff], '&Project/Git')
    Toolbar('Git', [cmd_refresh, cmd_stage_all, cmd_unstage_all, cmd_commit, cmd_diff])
    ContextMenu([cmd_stage, cmd_unstage], lambda context: context == 'SCRIPT')

    # register_load_model_callable(on_load_model)
    # register_unload_model_callable(on_unload_model)
else:
    log('Git client not initialized')
