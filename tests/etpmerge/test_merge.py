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
