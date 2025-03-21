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

"""Unregisters the Git extensions and utilities."""

import os
from pathlib import Path
import subprocess
import sys
from typing import Tuple

from ansys.scade.git import get_srg_name

APPDATA = os.getenv('APPDATA')
USERPROFILE = os.getenv('USERPROFILE')


def git_config() -> bool:
    """
    Update the global Git configuration.

    * Remove the declaration of merge tools
    * Unregister merge tools for targeted file extensions
    """

    def unregister_driver(id: str) -> bool:
        status = True
        for param in ['name', 'driver', 'trustExitCode']:
            cmd = ['git', 'config', '--global', '--unset', 'merge.%s.%s' % (id, param)]
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

    assert USERPROFILE
    status = True

    print('Git: unregister the etpmerge custom merge driver in Git global settings')
    if not unregister_driver('etpmerge'):
        status = False

    print('Git: unregister the amlgtmerge custom merge driver in Git global settings')
    if not unregister_driver('amlgtmerge'):
        status = False

    print('Git: unregister no diff for xscade files')
    if not unregister_driver('xscademerge'):
        status = False

    # unset git attributes
    gitattributes = Path(USERPROFILE, '.config', 'git', 'attributes')
    if gitattributes.exists():
        contents = gitattributes.read_text().strip('\n').split('\n')
        modified = False
        for extension in ['xscade', 'etp', 'almgt']:
            line = '*.{0} merge={0}merge'.format(extension)
            try:
                contents.remove(line)
                print('remove {} from global {}'.format(line, gitattributes))
                modified = True
            except ValueError:
                pass
        if modified:
            contents.append('')
            gitattributes.write_text('\n'.join(contents))
    return status


def unregister_srg_file(name: str):
    """Delete the srg file from Customize."""
    assert APPDATA
    dst = Path(APPDATA, 'SCADE', 'Customize', name)
    dst.unlink(missing_ok=True)


def scade_config():
    """Unregister the SCADE extension srg files."""
    unregister_srg_file(get_srg_name())


def unregister() -> Tuple[int, str]:
    """Implement the ``ansys.scade.registry/unregister`` entry point."""
    git_config()
    scade_config()
    return (0, '')


def main():
    """Implement the ``ansys.scade.wux.unregister`` packages's project script."""
    code, message = unregister()
    if message:
        print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == '__main__':
    code = main()
    sys.exit(code)
