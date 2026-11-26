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

"""Unit tests for almgtmerge3.py."""

from pathlib import Path
import sys

from lxml import etree as et
import pytest

from ansys.scade.git.almgtmerge.__main__ import main
from ansys.scade.git.almgtmerge.almgtmerge3 import merge3
from test_utils import cmp_file, get_resources_dir

almgtmerge_data_nominal = [
    (get_resources_dir() / 'almgtmerge' / 'resources' / 'Nominal'),
    (get_resources_dir() / 'almgtmerge' / 'resources' / 'DelBoth'),
]


@pytest.mark.parametrize(
    'dir',
    almgtmerge_data_nominal,
    ids=[Path(_).name for _ in almgtmerge_data_nominal],
)
def test_almgtmerge_nominal(capsys, dir, tmpdir):
    merge_args = [str(dir / (_ + '.almgt')) for _ in ['Local', 'Remote', 'Base']]
    # save the result to tmpdir
    result = tmpdir / (dir.name + 'Merge.almgt')
    merge_args.append(str(result))
    status = merge3(*merge_args)
    assert status

    # compare to the reference
    ref = dir / 'Merge.almgt'
    # a merge driver must not write to the standard output
    captured = capsys.readouterr()
    assert captured.out == ''
    diff = cmp_file(ref, result, n=0)
    # not captured, this the loop hereafter
    # stdout.writelines(diff)
    for line in diff:
        print(line, end='')
    captured = capsys.readouterr()
    assert captured.out == ''


almgtmerge_data_robustness = [
    (get_resources_dir() / 'almgtmerge' / 'resources' / 'OsError'),
]


@pytest.mark.parametrize(
    'dir',
    almgtmerge_data_robustness,
    ids=[Path(_).name for _ in almgtmerge_data_robustness],
)
def test_almgtmerge_robustness(capsys, dir, tmpdir):
    merge_args = [str(dir / (_ + '.almgt')) for _ in ['Local', 'Remote', 'Base']]
    # save the result to tmpdir
    result = str(tmpdir / (dir.name + 'Merge.almgt'))
    merge_args.append(result)
    status = merge3(*merge_args)
    assert not status


def write_almgt(path, objects):
    """Write an almgt file: objects is a dictionary object id: [(requirement id, attributes)]."""
    content = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<traceability>\n'
    for object_id, requirements in objects.items():
        content += '<object id="%s" pathName="P::%s/">\n' % (object_id, object_id)
        content += ''.join('<requirement id="%s"%s/>\n' % _ for _ in requirements)
        content += '</object>\n'
    path.write_text(content + '</traceability>\n', encoding='utf-8')
    return str(path)


def merge_almgt(tmpdir, local, remote, base):
    """Merge almgt files described as in write_almgt, return the requirements of the result."""
    args = [
        write_almgt(tmpdir / (n + '.almgt'), o)
        for n, o in [('Local', local), ('Remote', remote), ('Base', base)]
    ]
    merged = str(tmpdir / 'Merged.almgt')
    assert merge3(*args, merged)
    root = et.parse(merged).getroot()
    return {
        obj.get('id'): {_.get('id'): dict(_.attrib) for _ in obj.iter('requirement')}
        for obj in root.iter('object')
    }


LINK = ' traceType="ADD_LINK"'


def test_almgtmerge_requirement_without_trace_type(tmpdir):
    # the attribute traceType is not mandatory in the files, it must not be set to None
    # one requirement added to an existing object, another one to a new object
    merged = merge_almgt(
        tmpdir,
        local={'O1': [('R0', LINK)]},
        remote={'O1': [('R0', LINK), ('R1', '')], 'O2': [('R2', LINK)]},
        base={'O1': [('R0', LINK)]},
    )
    assert merged == {
        'O1': {'R0': {'id': 'R0', 'traceType': 'ADD_LINK'}, 'R1': {'id': 'R1'}},
        'O2': {'R2': {'id': 'R2', 'traceType': 'ADD_LINK'}},
    }


def test_almgtmerge_replaced_requirement(tmpdir):
    # the remote replaced the only requirement of an object: the new one must be kept
    # the object O2 is not modified by the remote
    merged = merge_almgt(
        tmpdir,
        local={'O1': [('R0', LINK)], 'O2': [('R5', LINK)]},
        remote={'O1': [('R1', LINK)], 'O2': [('R5', LINK)]},
        base={'O1': [('R0', LINK)], 'O2': [('R5', LINK)]},
    )
    assert merged == {
        'O1': {'R1': {'id': 'R1', 'traceType': 'ADD_LINK'}},
        'O2': {'R5': {'id': 'R5', 'traceType': 'ADD_LINK'}},
    }


def test_almgtmerge_replaced_requirement_locally_modified(tmpdir):
    # the local modifications of the object are preserved too
    merged = merge_almgt(
        tmpdir,
        local={'O1': [('R0', LINK), ('R2', LINK)]},
        remote={'O1': [('R1', LINK)]},
        base={'O1': [('R0', LINK)]},
    )
    assert set(merged['O1']) == {'R1', 'R2'}


@pytest.mark.parametrize(
    'dir, code',
    [(almgtmerge_data_nominal[0], 0), (almgtmerge_data_robustness[0], 1)],
    ids=['Nominal', 'OsError'],
)
def test_almgtmerge_main(monkeypatch, dir, code, tmpdir):
    # the command line tool reports the status to Git through its exit code
    result = str(tmpdir / (dir.name + 'Main.almgt'))
    argv = ['almgtmerge']
    for option, name in [('-l', 'Local'), ('-r', 'Remote'), ('-b', 'Base')]:
        argv += [option, str(dir / (name + '.almgt'))]
    monkeypatch.setattr(sys, 'argv', argv + ['-m', result])
    with pytest.raises(SystemExit) as exit_info:
        main()
    assert exit_info.value.code == code
