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

"""Registers the Git extensions and utilities."""

import os
from pathlib import Path
import subprocess
import sys

APPDATA = os.getenv('APPDATA')
USERPROFILE = os.getenv('USERPROFILE')


def git_config() -> bool:
    """
    Update the global Git configuration.

    * Declare merge tools
    * Register merge tools for targeted file extensions
    """

    def register_driver(id: str, name: str, path: str, trust_exit: bool) -> bool:
        status = True
        for param, value in [('name', name), ('driver', path), ('trustExitCode', trust_exit)]:
            cmd = ['git', 'config', '--global', 'merge.%s.%s' % (id, param), value]
            log = cmd[:-1] + ['"%s"' % cmd[-1]]
            print(' '.join(log))

            gitrun = subprocess.run(cmd, capture_output=True, text=True)
            if gitrun.stdout:
                print(gitrun.stdout)
            if gitrun.stderr:
                print(gitrun.stderr)
            if gitrun.returncode != 0:
                status = False
                print('Error: git config failed')

        return status

    # scripts directory in <python>/Scripts
    status = True
    exe = Path(sys.executable)
    if exe.parent.name == 'Scripts':
        # virtual environment
        scripts_dir = exe.parent
    else:
        # regular Python installation
        scripts_dir = exe.parent / 'Scripts'

    print('Git: register the etpmerge custom merge driver in Git global settings')
    driver = '"%s" -b %%O -l %%A -r %%B -m %%A' % (scripts_dir / 'etpmerge.exe')
    description = 'Merge for SCADE project files'
    if not register_driver('etpmerge', description, str(driver), 'true'):
        status = False

    print('Git: register the amlgtmerge custom merge driver in Git global settings')
    description = 'Merge for SCADE ALM Gateway not exported traceability files'
    driver = '"%s" -b %%O -l %%A -r %%B -m %%A' % (scripts_dir / 'amlgtmerge.exe')
    if not register_driver('amlgtmerge', description, str(driver), 'true'):
        status = False

    print('Git: register no diff for xscade files')
    driver = 'exit 1'
    if not register_driver('xscademerge', 'Merge for SCADE model files', driver, 'true'):
        status = False

    # set git attributes
    gitattributes = Path(USERPROFILE, '.config', 'git', 'attributes')
    gitattributes.parent.mkdir(parents=True, exist_ok=True)
    contents = gitattributes.open().read().split('\n') if gitattributes.exists() else []
    if contents and not contents[-1]:
        # remove trailing blank line
        contents = contents[:-1]
    modified = False
    for extension in ['xscade', 'etp', 'almgt']:
        line = '*.{0} merge={0}merge'.format(extension)
        if line not in contents:
            print('add {} in global {}'.format(line, gitattributes))
            contents.append(line)
            modified = True
    if modified:
        contents.append('')
        gitattributes.open('w').write('\n'.join(contents))

    return status


def register_srg_file(srg: Path, install: Path):
    """Copy the srg file to Customize and patch it with the installation directory."""
    text = srg.open().read()
    text = text.replace('%TARGETDIR%', install.as_posix())
    dst = Path(APPDATA, 'SCADE', 'Customize', srg.name)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.open('w').write(text)


def scade_config():
    """Register the SCADE extension srg files."""
    script_dir = Path(__file__).parent
    # registrations depending on Python interpreter
    python_version = str(sys.version_info.major) + str(sys.version_info.minor)
    register_srg_file(script_dir / ('git-%s.srg' % python_version), script_dir)
    # other registrations
    # None for now
    # register_srg_file(script_dir / 'git.srg', script_dir)


def main():
    """Register package."""
    git_config()
    scade_config()


if __name__ == '__main__':
    main()
