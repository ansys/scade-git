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

"""
Caches properties for etpmerge3.

* The local/remote entities have a property `_base` to refer to the
  corresponding base object, `None` if the object has been created
* Each project maintains
  * A dictionary of entities by id: `_map_ids`
  * A dictionary of file by pathname: `_map_files`
  * A list of folders: `_folders`
* Each container maintains a dictionary of children by key (name by default)
  * Project/Folder: `_map_folders`
  * Project: `_map_configurations`
  * Annotable: `_map_props`, the key is (<name>, <id configuration>)
"""

import scade.model.project.stdproject as std

from .utils import get_prop_key
from .visitor import Visit


class WrongBaseError(BaseException):
    """
    Error raised when two projects are not related.

    Parameters
    ----------
    project_entity : ProjectEntity
        Inconsistent project entity.
    """

    def __init__(self, project_entity: std.ProjectEntity):
        # store the inconsistent project entity
        self.project_entity = project_entity


class CacheMaps(Visit):
    """Visitor for creating the additional attributes of the project entities."""

    def __init__(self):
        """Declare global maps, to be accessed from any elements."""
        self.map_ids = None
        self.map_files = None

    def visit_project(self, project: std.Project):
        """Add the attributes for a project."""
        # the cache must be used once per project
        assert not hasattr(project, '_map_ids')
        # initialize the extra attributes tp be accessed during the visit
        project._map_ids = {}
        self.map_ids = project._map_ids
        project._map_files = {}
        self.map_files = project._map_files
        project._folders = []
        self.folders = project._folders

        project._map_configurations = {_.name: _ for _ in project.configurations}
        project._map_folders = {_.name: _ for _ in project.roots if isinstance(_, std.Folder)}

        # go
        super().visit_project(project)

    def visit_folder(self, folder: std.Folder):
        """Add the attributes for a folder."""
        folder._map_folders = {_.name: _ for _ in folder.elements if isinstance(_, std.Folder)}
        self.folders.append(folder)
        super().visit_folder(folder)

    def visit_file_ref(self, file_ref: std.FileRef):
        """Add the attributes for a file."""
        self.map_files[file_ref.pathname] = file_ref
        super().visit_file_ref(file_ref)

    def visit_annotable(self, annotable: std.Annotable):
        """Add the attributes for an annotatable entity."""
        annotable._map_props = {get_prop_key(_): _ for _ in annotable.props}
        super().visit_annotable(annotable)

    def visit_project_entity(self, project_entity: std.ProjectEntity):
        """Add the attributes for a project entity."""
        self.map_ids[project_entity.id] = project_entity
        super().visit_project_entity(project_entity)


class CacheBase(Visit):
    """
    Visitor for mapping the elements of a local or remote project to a base project.

    Parameters
    ----------
    base : std.Project
        Configuration to copy to the local project.
    """

    def __init__(self, base: std.Project):
        """Initialize the visitor and stores the reference to the base project."""
        self.base = base
        # stack, for folder resolution
        self.hierarchy = []

    def visit_configuration(self, configuration: std.Configuration):
        """
        Resolve a configuration by id only.

        Resolution by name is a very unlikely use case which
        causes a lot of issues for references: properties, etc.
        """
        self.resolve_by_id(configuration)
        super().visit_configuration(configuration)

    def visit_folder(self, folder: std.Folder):
        """Resolve a folder by id, or by name in its owner's base."""
        if not self.resolve_by_id(folder):
            # cut/paste issue? try by name...
            owner_base = self.hierarchy[-1]._base
            if owner_base:
                folder._base = owner_base._map_folders.get(folder.name)
        self.hierarchy.append(folder)
        super().visit_folder(folder)
        self.hierarchy.pop()

    def visit_file_ref(self, file_ref: std.FileRef):
        """Resolve a file by id or by pathname."""
        if not self.resolve_by_id(file_ref):
            # cut/paste issue? try by name...
            file_ref._base = self.base._map_files.get(file_ref.pathname)
        super().visit_file_ref(file_ref)

    def visit_project(self, project: std.Project):
        """Initialize the current folder hierarchy with the project."""
        assert self.resolve_by_id(project)
        self.hierarchy.append(project)
        super().visit_project(project)
        self.hierarchy.pop()

    def visit_prop(self, prop: std.Prop):
        """Resolve a property by id, or by key in its owner's base."""
        if not self.resolve_by_id(prop):
            # unset/set issue? try by key...
            # TODO: consider configuration._base's id?
            if prop.entity._base:
                prop._base = prop.entity._base._map_props.get(get_prop_key(prop))
        super().visit_prop(prop)

    # helper
    def resolve_by_id(self, project_entity: std.ProjectEntity) -> bool:
        """
        Search for the base entity of a local or a remote one by Id.

        Update the attributes `_base` with the found entity and when not None,
        make sure it has at least the same type.

        Parameters
        ----------
        project_entity : ProjectEntity
            Entity to search in the base project.

        Returns
        -------
        bool
            Whether a corresponding entity has been found.
        """
        base = self.base._map_ids.get(project_entity.id)
        if base and type(base) is not type(project_entity):
            # both projects are unrelated: garbage in...
            raise WrongBaseError(project_entity)

        # the cache must be used once per project
        assert not hasattr(project_entity, '_base')
        project_entity._base = base
        return base is not None
