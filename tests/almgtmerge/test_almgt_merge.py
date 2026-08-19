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

import pytest

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
    # ignore banner if any
    captured = capsys.readouterr()
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
