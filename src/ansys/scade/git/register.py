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

"""Registers the Git extensions and utilities."""

try:
    import importlib.metadata as importlib_metadata
except ModuleNotFoundError:
    import importlib_metadata
import os
from pathlib import Path
import shutil
import subprocess  # nosec B404  # used to call git config
import sys
from typing import List, Optional, Tuple

from ansys.scade.git import get_srg_name

# APPDATA must be defined
APPDATA = os.environ['APPDATA']
# USERPROFILE must be defined
USERPROFILE = os.environ['USERPROFILE']


def find_script(name: str) -> Optional[Path]:
    """
    Return the path of the console script installed with this package.

    ``sys.executable`` cannot be used to locate the scripts: when the registration is
    run by SCADE, it is the SCADE host, and ``pip install --user`` installs the
    scripts outside of the interpreter's directory.

    Parameters
    ----------
    name : str
        Name of the script, without extension.
    """
    exe_name = '%s.exe' % name
    try:
        files = importlib_metadata.distribution('ansys-scade-git').files or []
        for file in files:
            if file.name.lower() == exe_name:
                path = Path(file.locate()).resolve()  # type: ignore
                if path.exists():
                    return path
    except importlib_metadata.PackageNotFoundError:
        pass

    # not installed from a distribution, look in the path and the interpreter's directory
    which = shutil.which(name)
    if which:
        return Path(which)
    exe = Path(sys.executable)
    scripts_dir = exe.parent if exe.parent.name == 'Scripts' else exe.parent / 'Scripts'
    path = scripts_dir / exe_name
    return path if path.exists() else None


def git_config() -> bool:
    """
    Update the global Git configuration.

    * Declare merge tools
    * Register merge tools for targeted file extensions
    """

    def register_driver(id: str, name: str, path: str, trust_exit: str) -> bool:
        status = True
        for param, value in [('name', name), ('driver', path), ('trustExitCode', trust_exit)]:
            cmd = ['git', 'config', '--global', 'merge.%s.%s' % (id, param), value]
            log = cmd[:-1] + ['"%s"' % cmd[-1]]
            print(' '.join(log))

            gitrun = subprocess.run(cmd, capture_output=True, text=True)  # nosec B603  # inputs checked
            if gitrun.stdout:
                print(gitrun.stdout)
            if gitrun.stderr:
                print(gitrun.stderr)
            if gitrun.returncode != 0:
                status = False
                print('Error: git config failed')

        return status

    status = True

    def register_merge_script(id: str, description: str) -> bool:
        script = find_script(id)
        if script is None:
            print('Error: the script %s.exe is not found, the merge driver is not registered' % id)
            return False
        driver = '"%s" -b %%O -l %%A -r %%B -m %%A' % script
        return register_driver(id, description, driver, 'true')

    print('Git: register the etpmerge custom merge driver in Git global settings')
    if not register_merge_script('etpmerge', 'Merge for SCADE project files'):
        status = False

    print('Git: register the almgtmerge custom merge driver in Git global settings')
    description = 'Merge for SCADE ALM Gateway not exported traceability files'
    if not register_merge_script('almgtmerge', description):
        status = False

    print('Git: register no diff for xscade files')
    driver = 'exit 1'
    if not register_driver('xscademerge', 'Merge for SCADE model files', driver, 'true'):
        status = False

    # set git attributes
    gitattributes = Path(USERPROFILE, '.config', 'git', 'attributes')
    gitattributes.parent.mkdir(parents=True, exist_ok=True)
    contents, newline = read_lines(gitattributes)
    modified = False
    for extension in ['xscade', 'etp', 'almgt']:
        line = '*.{0} merge={0}merge'.format(extension)
        if line not in contents:
            print('add {} in global {}'.format(line, gitattributes))
            contents.append(line)
            modified = True
    if modified:
        write_lines(gitattributes, contents, newline)

    return status


def read_lines(path: Path) -> Tuple[List[str], str]:
    """
    Return the lines of a UTF-8 text file, and its line ending.

    The line ending is returned to be able to write the file back without changing it.
    The file is created with LF line endings, supported by Git, when it does not exist.

    Parameters
    ----------
    path : Path
        Path of the file, which may not exist.
    """
    if not path.exists():
        return [], '\n'
    text = path.read_bytes().decode('utf-8')
    lines = text.splitlines()
    while lines and not lines[-1]:
        lines.pop()
    return lines, '\r\n' if '\r\n' in text else '\n'


def write_lines(path: Path, lines: List[str], newline: str):
    """
    Write lines to a UTF-8 text file, each line being terminated by `newline`.

    Parameters
    ----------
    path : Path
        Path of the file.
    lines : List[str]
        Lines to write.
    newline : str
        Line ending.
    """
    path.write_bytes(''.join(line + newline for line in lines).encode('utf-8'))


def register_srg_file(srg: Path, install: Path):
    """
    Copy the srg file to Customize and patch it with the installation directory.

    The files are read and written with the system's encoding, as expected by SCADE.
    """
    text = srg.read_text()
    text = text.replace('%TARGETDIR%', install.as_posix())
    dst = Path(APPDATA, 'SCADE', 'Customize', srg.name)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(text)


def scade_config():
    """Register the SCADE extension srg files."""
    script_dir = Path(__file__).parent
    register_srg_file(script_dir / get_srg_name(), script_dir)


def register() -> Tuple[int, str]:
    """Implement the ``ansys.scade.registry/register`` entry point."""
    status = git_config()
    scade_config()
    if not status:
        return (1, 'Error: the Git configuration is incomplete, see the messages above')
    return (0, '')


def main():
    """Implement the ``ansys.scade.git.register`` packages's project script."""
    code, message = register()
    if message:
        print(message, file=sys.stderr if code else sys.stdout)
    return code


if __name__ == '__main__':
    code = main()
    sys.exit(code)
