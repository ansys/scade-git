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

"""Provides create/delete/copy functions for project entities."""

import _scade_api
import scade.model.project.stdproject as std


def create_folder(owner: std.ProjectEntity, name: str, extensions: str = '') -> std.Folder:
    """
    Create a Folder instance.

    Parameters
    ----------
    owner : ProjectEntity
        Owner of the folder: Either the project or a folder.
    name : str
        Name of the folder.
    extensions : str
        Optional filter for browsing for added files.

    Returns
    -------
    New Folder instance
    """
    if isinstance(owner, std.Project):
        folder = std.Folder(owner)
        folder.owner = owner
    else:
        folder = std.Folder(owner.project)
        folder.folder = owner
    folder.name = name
    folder.extensions = extensions

    return folder


def create_configuration(owner: std.Project, name: str) -> std.Configuration:
    """
    Create a Configuration instance.

    Parameters
    ----------
    owner : Project
        Project owning the configuration.
    name : str
        Name of the configuration.

    Returns
    -------
    New Configuration instance
    """
    configuration = std.Configuration(owner)
    configuration.project = owner
    configuration.name = name

    return configuration


def create_file_ref(owner: std.ProjectEntity, persist_as: str) -> std.FileRef:
    """
    Create a FileRef instance.

    Parameters
    ----------
    owner : ProjectEntity
        Owner of the file: Either the project or a folder.
    persist_as : str
        Reference to the file to be stored, optionally relative to the project.

    Returns
    -------
    New FileRef instance
    """
    if isinstance(owner, std.Project):
        file_ref = std.FileRef(owner)
        file_ref.owner = owner
    else:
        file_ref = std.FileRef(owner.project)
        file_ref.folder = owner
    file_ref.persist_as = persist_as

    return file_ref


def create_prop(
    owner: std.Annotable, configuration: std.Configuration, name: str, values
) -> std.Prop:
    """
    Create a Prop instance.

    Parameters
    ----------
    owner : ProjectEntity
        Owner of the property: Either the project, a file or a folder.
    name : str
        Name of the property.
    configuration : Configuration
        Optional configuration linked to the property.
    values : List[str]
        Values of the property.

    Returns
    -------
    New Prop instance
    """
    if isinstance(owner, std.Project):
        project = owner
    else:
        project = owner.project

    prop = std.Prop(project)
    prop.entity = owner
    prop.name = name
    prop.values = values
    if configuration is not None:
        prop.configuration = configuration

    return prop


def copy_configuration(configuration: std.Configuration, owner: std.Project) -> std.Configuration:
    """
    Copy a configuration from the remote project to the local project.

    Set the configuration's attribute _local to the new configuration.

    Parameters
    ----------
    configuration : Configuration
        Configuration to copy to the local project.
    owner : Project
        Remote project.

    Returns
    -------
    New configuration instance
    """
    copy = create_configuration(owner, configuration.name)
    copy._base = configuration._base
    configuration._local = copy
    return copy


def copy_folder(folder: std.Folder, owner: std.ProjectEntity) -> std.Folder:
    """
    Copy a folder, and its properties, from the remote project to the local project.

    Set the folder's attribute _local to the new folder.

    Parameters
    ----------
    folder : Folder
        Folder to copy to the local project.
    owner : ProjectEntity
        Owner of the folder: Either the project or a folder.

    Returns
    -------
    New Folder instance
    """
    copy = create_folder(owner, folder.name, extensions=folder.extensions)
    copy._base = folder._base
    folder._local = copy
    for prop in folder.props:
        copy_prop(prop, copy)
    copy._map_folders = {}
    copy._map_props = {}
    return copy


def copy_file_ref(file_ref: std.FileRef, owner: std.ProjectEntity) -> std.FileRef:
    """
    Copy a file, and its properties, from the remote project to the local project.

    Set the file's attribute _local to the new file.

    Parameters
    ----------
    file_ref : FileRef
        File to copy to the local project.
    owner : ProjectEntity
        Owner of the file: Either the project or a folder.

    Returns
    -------
    New FileRef instance
    """
    copy = create_file_ref(owner, file_ref.persist_as)
    copy._base = file_ref._base
    file_ref._local = copy
    for prop in file_ref.props:
        copy_prop(prop, copy)
    copy._map_props = {}
    return copy


def copy_prop(prop: std.Prop, owner: std.Annotable) -> std.Prop:
    """
    Copy a property from the remote project to the local project.

    Set the property's attribute _local to the new property.
    Set the new property's configuration to its configuration's local.

    Parameters
    ----------
    prop : Prop
        Property to copy to the local project.
    owner : Annotable
        Owner of the property.

    Returns
    -------
    New Prop instance
    """
    # note: if/else rather than =/if/else for code coverage
    if prop.configuration:
        configuration = prop.configuration._local
    else:
        configuration = None
    copy = create_prop(owner, configuration, prop.name, prop.values)
    copy._base = prop._base
    prop._local = copy
    return copy


def delete_configuration(configuration: std.Configuration):
    """
    Remove a configuration from its projectas wekll as its linked properties.

    Parameters
    ----------
    configuration : Configuration
        Configuration to disconnect.

    Returns
    -------
    None
    """
    # remove the configuration from its project
    _scade_api.remove(configuration.project, 'configuration', configuration)
    # remove the properties from the entities
    for prop in configuration.props.copy():
        _scade_api.remove(prop.entity, 'prop', prop)


def delete_prop(prop: std.Prop):
    """
    Remove a property from its owner.

    Parameters
    ----------
    prop : Prop
        Property to disconnect.

    Returns
    -------
    None
    """
    # remove the property from its owner and optional configuration
    _scade_api.remove(prop.entity, 'prop', prop)
    # remove the properties from the configuration
    if prop.configuration:
        _scade_api.remove(prop.configuration, 'prop', prop)


def delete_folder(folder: std.Folder):
    """
    Remove a folder from its owner.

    Parameters
    ----------
    folder : Folder
        Folder to disconnect.

    Returns
    -------
    None
    """
    # remove the folder from its owner
    if folder.folder:
        _scade_api.remove(folder.folder, 'element', folder)
    else:
        _scade_api.remove(folder.owner, 'root', folder)
    # do not propagate to the contained elements:
    # they can't be accessed from the project anymore, thus won't be saved


def delete_file_ref(file_ref: std.FileRef):
    """
    Remove a file from its owner.

    Parameters
    ----------
    file_ref : FileRef
        File to disconnect.

    Returns
    -------
    None
    """
    # remove the file from its owner
    if file_ref.folder:
        _scade_api.remove(file_ref.folder, 'element', file_ref)
    else:
        _scade_api.remove(file_ref.owner, 'root', file_ref)
    # do not propagate to the properties:
    # they can't be accessed from the project anymore, thus won't be saved


def move_element(element: std.Element, target: std.ProjectEntity):
    """
    Move an element into a new container.

    Parameters
    ----------
    element : Element
        Element to move.
    target : ProjectEntity
        New owner of the element, either a project or a folder

    Returns
    -------
    None
    """
    if element.folder:
        _scade_api.remove(element.folder, 'element', element)
    else:
        _scade_api.remove(element.owner, 'root', element)
    if isinstance(target, std.Folder):
        _scade_api.add(target, 'element', element)
    else:
        _scade_api.add(target, 'root', element)
