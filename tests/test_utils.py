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

"""Helpers for test_*.py."""

import difflib
from pathlib import Path
from subprocess import run
from typing import Optional


def get_resources_dir() -> Path:
    """Return the directory ./resources relative to this file's directory."""
    script_path = Path(__file__)
    return script_path.parent


def cmp_log(log_file, lines) -> bool:
    """Return True if the file is identical to a list of strings."""
    log_lines = list(open(log_file))
    log_lines = [line.strip('\n') for line in log_lines]
    return log_lines == lines


def cmp_file(fromfile: Path, tofile: Path, n=3, linejunk=None):
    """Return the differences between two files."""
    with fromfile.open() as fromf, tofile.open() as tof:
        if linejunk:
            fromlines = [line for line in fromf if not linejunk(line)]
            tolines = [line for line in tof if not linejunk(line)]
        else:
            fromlines, tolines = list(fromf), list(tof)

    diff = difflib.context_diff(fromlines, tolines, str(fromfile), str(tofile), n=n)
    return diff


def run_git(command: str, *args: str, dir: Optional[Path] = None) -> bool:
    """Run a git command."""
    cmd = ['git']
    if dir:
        cmd.append('--work-tree=%s' % dir)
        cmd.append('--git-dir=%s/.git' % dir)
    cmd.append(command)
    cmd += list(args)
    cp = run(cmd, capture_output=True, text=True)
    if cp.stdout:
        print(cp.stdout)
    if cp.stderr:
        print(cp.stderr)
    return cp.returncode == 0


def git_restore(pathspec: str) -> bool:
    """Discard changes to a file or a directory."""
    return run_git('restore', '--worktree', '--staged', pathspec)
