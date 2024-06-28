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

"""Provides helpers for reporting and computations."""

from typing import Any

import scade.model.project.stdproject as std


def get_prop_key(prop: std.Prop, configuration: std.Configuration = None) -> Any:
    """
    Return the key to find a prop by name: (name, configuration's id).

    Parameters
    ----------
    prop : std.Prop
        Input property.
    configuration : std.Configuration
        When not None, it is the configuration to consider instead of the one linked
        to the property. This is usually the property's configuration's local.

    Returns
    -------
    Local key for the property.
    """
    if not configuration:
        configuration = prop.configuration
    # note: if/else rather than =/if/else for code coverage
    if configuration:
        id = configuration.id
    else:
        # several instances of this property with same name
        # use the first value (tool's name) as secondary key
        # note: if/else rather than =/if/else for code coverage
        if prop.name == '@STUDIO:TOOLCONF':
            id = prop.values[0]
        else:
            id = None
    return prop.name, id


def get_context(entity: std.ProjectEntity) -> str:
    """
    Return a string describing the object, usually composed of its class, name and id.

    The context is extended with the owner's context for properties.

    Parameters
    ----------
    entity : std.ProjectEntity

    Returns
    -------
    str
        Readable description of the entity
    """
    context = '%s "%d" ("%s")' % (type(entity).__name__, entity.id, get_name(entity))
    if isinstance(entity, std.Prop):
        context += '\n    from: ' + get_context(entity.entity)
    return context


def get_name(entity: std.ProjectEntity) -> str:
    """
    Return the name of the entity.

    The name of projects and files is the base name, with the extension.

    Parameters
    ----------
    entity : std.ProjectEntity

    Returns
    -------
    str
        Name of the entity.
    """
    if isinstance(entity, std.Project):
        # path not meaningful, at least with Git
        # return Path(entity.pathname).name
        return '<project>'
    else:
        # all other classes have an attribute name
        return entity.name


def get_element_owner(element: std.Element) -> std.ProjectEntity:
    """
    Return the owner of the element.

    The owner can be either a project or a folder.

    Parameters
    ----------
    element : std.Element

    Returns
    -------
    std.ProjectEntity
        Owner of the entity.
    """
    # note: if/else rather than =/if/else for code coverage
    if element.folder:
        return element.folder
    else:
        return element.owner
