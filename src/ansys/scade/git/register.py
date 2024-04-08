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

TEMPLATE_FILE = """
[Studio/Work Interfaces/ansys-scade-__extension_name__37]
"Pathname"="ETCUST.DLL"
"Version"="19400"
"Expire"="23200"

[Custom/Studio/Extensions/ansys-scade-__extension_name__37]
"Pathname"="%APPDATA%/Python/Python37/site-packages/ansys/scade/__extension_name__/__extension_name__.py"

[Studio/Work Interfaces/ansys-scade-__extension_name__310]
"Pathname"="ETCUST.DLL"
"Version"="23200"
"Expire"="24200"

[Custom/Studio/Extensions/ansys-scade-__extension_name__310]
"Pathname"="%APPDATA%/Python/Python310/site-packages/ansys/scade/__extension_name__/__extension_name__.py"
"""


def git_config() -> bool:
    """
    Update the global Git configuration.

    * Declare merge tools
    * Register merge tools for targeted files
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
    if not register_driver('etpmerge', 'Merge for SCADE project files', str(driver), 'true'):
        status = False

    print('Git: register no diff for xscade files')
    driver = 'exit 1'
    if not register_driver('xscademerge', 'Merge for SCADE model files', driver, 'true'):
        status = False

    # set git attributes
    gitattributes = Path(USERPROFILE, '.config', 'git', 'attributes')
    gitattributes.parent.mkdir(parents=True, exist_ok=True)
    with gitattributes.open(mode='a+') as f:
        f.seek(0)
        contents = f.readlines()
        prefix = '\n' if contents and contents[-1] and contents[-1][-1] != '\n' else ''
        etpmerge = False
        xscademerge = False
        for line in contents:
            if line.strip() == '*.etp merge=etpmerge':
                etpmerge = True
            if line.strip() == '*.xscade merge=xscademerge':
                xscademerge = True
        if not etpmerge:
            print('add "*.etp merge=etpmerge" in global {}'.format(gitattributes))
            f.write('%s*.etp merge=etpmerge\n' % prefix)
            prefix = ''
        else:
            print('line "*.etp merge=etpmerge" exists in global {}'.format(gitattributes))
        if not xscademerge:
            print('add "*.xscade merge=xscademerge" in global {}'.format(gitattributes))
            f.write('%s*.xscade merge=xscademerge\n' % prefix)
            prefix = ''
        else:
            print('line "*.xscade merge=xscademerge" exists in global {}'.format(gitattributes))

    return status


def remove_prefix(text: str, prefix: str):
    """TODO."""
    if text.startswith(prefix):
        return text[len(prefix) :]
    return None


def create_srg_file(extension_name):
    """Register the SCADE extension srg file."""
    # Then get the template, replace the content and write to the right place
    template = TEMPLATE_FILE

    template = template.replace("__extension_name__", extension_name)
    srg_filename = os.path.join(APPDATA, 'SCADE', 'Customize', extension_name + '.srg')

    with open(srg_filename, "w") as f:
        f.write(template)


def main():
    """Register package."""
    git_config()


    if False:
        # TODO: patch existing srg files with target directory instead of generating them
        # registration script installed in <python>/Lib/site_packages/ansys/scade/git
        script_path = Path(__file__)
        script_name = script_path.stem
        extension_name = remove_prefix(script_name, 'register_ansys_scade_')
        if extension_name:
            create_srg_file(extension_name)
            print('Registered extension ansys.scade.{}'.format(extension_name))
        else:
            print('Failed to register extension ansys.scade.{}'.format(extension_name))


if __name__ == '__main__':
    main()
