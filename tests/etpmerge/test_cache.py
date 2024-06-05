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

"""Unit tests for etpmerge3.py."""

import pytest

from ansys.scade.git.etpmerge.cache import CacheBase, CacheMaps
from test_utils import get_resources_dir


@pytest.mark.parametrize(
    'lrb',
    [
        (get_resources_dir() / 'etpmerge' / 'resources' / 'Identical'),
    ],
    indirect=True,
)
def test_cache_maps(capsys, lrb, tmpdir):
    local, remote, base = lrb
    # run the cache on the base project
    CacheMaps().visit(base)
    assert len(base.file_refs) == len(base._map_files)


@pytest.mark.parametrize(
    'lrb',
    [
        (get_resources_dir() / 'etpmerge' / 'resources' / 'Identical'),
    ],
    indirect=True,
)
def test_cache_base_base(capsys, lrb, tmpdir):
    local, remote, base = lrb
    # run the cache on the base
    CacheMaps().visit(base)
    # run the cache base/base
    CacheBase(base).visit(base)
    # save the list of entities
    entities = base._map_ids.values()
    # make sure all the items have been found
    for entity in entities:
        assert entity._base == entity


@pytest.mark.parametrize(
    'lrb',
    [
        (get_resources_dir() / 'etpmerge' / 'resources' / 'Identical'),
    ],
    indirect=True,
)
def test_cache_base(capsys, lrb, tmpdir):
    local, remote, base = lrb
    # run the cache on the loaded projects
    CacheMaps().visit(base)
    CacheMaps().visit(local)
    CacheMaps().visit(remote)
    # run the cache against base for both projects
    # since the models are identical, each instance shall
    # have a corresponding one in the base project for both
    # local and remote projects
    for project in local, remote:
        CacheBase(base).visit(project)
        for entity in project._map_ids.values():
            assert entity._base is not None
