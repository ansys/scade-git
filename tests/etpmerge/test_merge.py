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

"""Unit tests for etpmerge3.py."""

from pathlib import Path

import pytest

from ansys.scade.git.etpmerge import etpmerge3
from ansys.scade.git.etpmerge.etpmerge3 import EtpMerge3
from test_utils import cmp_file, get_resources_dir

etpmerge_data = [
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Identical'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Configurations'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Properties'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Folders'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Files'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Hierarchy'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Advanced'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Tools'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Crlf'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Lf'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'WrongBase'),
    (get_resources_dir() / 'etpmerge' / 'resources' / 'Issue1'),
    # failed tests to be analyzed
    # (get_resources_dir() / 'resources' / 'Issue2'),
    # (get_resources_dir() / 'resources' / 'Issue3'),
]


@pytest.mark.parametrize(
    'lrb',
    etpmerge_data,
    ids=[Path(_).name for _ in etpmerge_data],
    indirect=True,
)
def test_etpmerge(capsys, lrb, tmpdir):
    local, remote, base = lrb
    # save the result to tmpdir
    basename = Path(base.pathname).parent.stem + '.etp'
    result = tmpdir / basename
    etp = EtpMerge3(local, remote, base)
    etp.merge3(str(result))

    # compare to the reference
    ref = Path(base.pathname).with_name('Merge.etp')
    # ignore banner if any
    captured = capsys.readouterr()
    diff = cmp_file(ref, result, n=0)
    # not captured, this the loop hereafter
    # stdout.writelines(diff)
    for line in diff:
        print(line, end='')
    captured = capsys.readouterr()
    assert captured.out == ''


class _Stub:
    """Hashable object with arbitrary attributes."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def test_etpmerge_duplicated_property(capsys, monkeypatch):
    # two remote properties matching the same local one
    local_prop = _Stub(name='PROP', id=7, _base=None)
    local_entity = _Stub(props=[local_prop], _map_props={'key': local_prop})
    remote_props = [_Stub(configuration=None, _base=None) for _ in range(2)]
    remote_entity = _Stub(_local=local_entity, props=remote_props)
    monkeypatch.setattr(etpmerge3, 'get_prop_key', lambda prop, configuration: 'key')

    etp = object.__new__(EtpMerge3)
    merged = []
    monkeypatch.setattr(etp, 'merge_values', lambda local, remote: merged.append(remote))
    etp.merge_properties(remote_entity)  # type: ignore

    # the values are merged, the warning does not pollute the standard output
    assert merged == remote_props
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == 'Duplicated property PROP (7)\n'


@pytest.mark.parametrize('crlf', [False, True], ids=['Lf', 'Crlf'])
def test_etpmerge_save_utf8(tmp_path, crlf):
    # the local project is saved by SCADE: UTF-8 with CRLF on Windows
    saved = '<?xml version="1.0" encoding="UTF-8"?>\r\n<Prop name="modifi\u00e9"/>\r\n'
    newline = b'\r\n' if crlf else b'\n'
    local = tmp_path / 'Local.etp'
    local.write_bytes(b'<Project/>' + newline)

    def save(pathname):
        Path(pathname).write_bytes(saved.encode('utf-8'))

    etp = object.__new__(EtpMerge3)
    etp.local = _Stub(pathname=str(local), save=save)  # type: ignore
    # the names in the conflicts may contain non-ASCII characters
    etp.conflicts = [('context \u00e9', 'local \u00e0', 'remote \u00fc')]  # type: ignore
    merged = tmp_path / 'Merged.etp'
    etp.save(str(merged))

    expected = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<Prop name="modifi\u00e9"/>',
        '<<<<<<< HEAD',
        'context \u00e9',
        'local \u00e0',
        '=======',
        'remote \u00fc',
        '>>>>>>>',
    ]
    content = merged.read_bytes()
    assert content == ''.join(_ + newline.decode() for _ in expected).encode('utf-8')
    assert not (tmp_path / 'Merged.etp.etp').exists()
