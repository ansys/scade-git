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

"""Tests for the registration of the merge drivers."""

from pathlib import Path
import sys

import pytest

import ansys.scade.git.register as register
import ansys.scade.git.unregister as unregister


def test_find_script_independent_of_interpreter(monkeypatch, tmp_path):
    # SCADE runs the registration with its own interpreter,
    # which is not the one the package is installed for
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'host' / 'python.exe'))
    script = register.find_script('etpmerge')
    if script is None:
        pytest.skip('the package scripts are not installed')
    assert script.name.lower() == 'etpmerge.exe'
    assert script.exists()
    assert tmp_path not in Path(script).parents


def test_find_script_unknown(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, 'executable', str(tmp_path / 'python.exe'))
    assert register.find_script('not_a_scade_git_script') is None


def test_git_config_missing_script(monkeypatch, capsys, tmp_path):
    class Run:
        stdout = stderr = ''
        returncode = 0

    calls = []
    monkeypatch.setattr(register, 'find_script', lambda name: None)
    monkeypatch.setattr(register.subprocess, 'run', lambda cmd, **kw: calls.append(cmd) or Run())
    monkeypatch.setattr(register, 'USERPROFILE', str(tmp_path))
    assert not register.git_config()
    assert 'etpmerge.exe is not found' in capsys.readouterr().out
    # no driver is declared for the missing scripts
    assert not any('merge.etpmerge' in ' '.join(_) for _ in calls)
    assert not any('merge.almgtmerge' in ' '.join(_) for _ in calls)


def test_unregister_removes_legacy_driver(monkeypatch, tmp_path):
    # the driver was registered as 'amlgtmerge' up to 0.3.1
    class Run:
        stdout = stderr = ''

        def __init__(self, returncode):
            self.returncode = returncode

    calls = []

    def run(cmd, **kw):
        calls.append(' '.join(cmd))
        # git config --unset fails for the legacy driver when it is not registered
        return Run(5 if 'merge.amlgtmerge' in ' '.join(cmd) else 0)

    monkeypatch.setattr(unregister.subprocess, 'run', run)
    monkeypatch.setattr(unregister, 'USERPROFILE', str(tmp_path))
    assert unregister.git_config()
    assert any('--unset merge.amlgtmerge.driver' in _ for _ in calls)
    assert any('--unset merge.almgtmerge.driver' in _ for _ in calls)


@pytest.mark.parametrize('module', [register, unregister])
@pytest.mark.parametrize('git_status', [True, False])
def test_registration_reports_git_config_status(monkeypatch, module, git_status):
    scade_calls = []
    monkeypatch.setattr(module, 'git_config', lambda: git_status)
    monkeypatch.setattr(module, 'scade_config', lambda: scade_calls.append(True))
    code, message = (module.register if module is register else module.unregister)()
    assert code == (0 if git_status else 1)
    assert bool(message) != git_status
    # the SCADE registration is independent of the Git configuration
    assert scade_calls


def test_unregister_not_registered_is_not_an_error(monkeypatch, tmp_path):
    class Run:
        stdout = stderr = ''
        # git config --unset: the key is not set
        returncode = 5

    monkeypatch.setattr(unregister.subprocess, 'run', lambda cmd, **kw: Run())
    monkeypatch.setattr(unregister, 'USERPROFILE', str(tmp_path))
    assert unregister.git_config()


def test_unregister_git_failure(monkeypatch, tmp_path):
    class Run:
        stdout = stderr = ''
        # git config: invalid config file
        returncode = 3

    monkeypatch.setattr(unregister.subprocess, 'run', lambda cmd, **kw: Run())
    monkeypatch.setattr(unregister, 'USERPROFILE', str(tmp_path))
    assert not unregister.git_config()


@pytest.fixture
def git_attributes(monkeypatch, tmp_path) -> Path:
    """Mock the calls to Git, and return the path of the attributes file."""

    class Run:
        stdout = stderr = ''
        returncode = 0

    monkeypatch.setattr(register, 'find_script', lambda name: tmp_path / (name + '.exe'))
    monkeypatch.setattr(register.subprocess, 'run', lambda cmd, **kw: Run())
    monkeypatch.setattr(unregister.subprocess, 'run', lambda cmd, **kw: Run())
    monkeypatch.setattr(register, 'USERPROFILE', str(tmp_path))
    monkeypatch.setattr(unregister, 'USERPROFILE', str(tmp_path))
    return tmp_path / '.config' / 'git' / 'attributes'


def test_attributes_new_file(git_attributes):
    assert register.git_config()
    assert git_attributes.read_bytes() == (
        b'*.xscade merge=xscademerge\n*.etp merge=etpmerge\n*.almgt merge=almgtmerge\n'
    )
    assert unregister.git_config()
    assert git_attributes.read_bytes() == b''


@pytest.mark.parametrize('newline', [b'\n', b'\r\n'])
def test_attributes_preserve_contents(git_attributes, newline):
    # the line endings and the non-ASCII characters of the user's file are preserved
    user = [b'# fichier modifi\xc3\xa9', b'*.png binary', b'*.etp merge=etpmerge']
    git_attributes.parent.mkdir(parents=True)
    git_attributes.write_bytes(newline.join(user) + newline)

    assert register.git_config()
    expected = user + [b'*.xscade merge=xscademerge', b'*.almgt merge=almgtmerge']
    assert git_attributes.read_bytes() == newline.join(expected) + newline

    assert unregister.git_config()
    assert git_attributes.read_bytes() == newline.join(user[:2]) + newline


def test_unregister_srg_file_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(unregister, 'APPDATA', str(tmp_path))
    # no error if the file does not exist
    unregister.unregister_srg_file('git.srg')
    dst = tmp_path / 'SCADE' / 'Customize' / 'git.srg'
    dst.parent.mkdir(parents=True)
    dst.write_text('')
    unregister.unregister_srg_file('git.srg')
    assert not dst.exists()


def test_register_srg_file(monkeypatch, tmp_path):
    monkeypatch.setattr(register, 'APPDATA', str(tmp_path))
    srg = tmp_path / 'git.srg'
    srg.write_text('"Package"="%TARGETDIR%/extension"\n')
    register.register_srg_file(srg, tmp_path / 'install')
    dst = tmp_path / 'SCADE' / 'Customize' / 'git.srg'
    assert dst.read_text() == '"Package"="%s/extension"\n' % (tmp_path / 'install').as_posix()
