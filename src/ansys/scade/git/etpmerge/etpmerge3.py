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

"""Merge3 for SCADE project files (ETP)."""

import os
from pathlib import Path
import traceback
from typing import Set

import scade.model.project.stdproject as std

import ansys.scade.git.etpmerge.fi as fi

from .cache import CacheBase, CacheMaps, WrongBaseError
from .utils import get_context, get_element_owner, get_name, get_prop_key


class EtpMerge3:
    """
    Merge the remote project to the local project and store the list of conflicts.

    Parameters
    ----------
    local : Project
        Local project in the working area.
    remote : Project
        Remote project to be merged.
    base : Project
        Common ancestor project of the projects being merged.
    """

    def __init__(self, local: std.Project, remote: std.Project, base: std.Project):
        """Store the references to the projects and initialize the dynamic variables."""
        # projects
        self.local = local
        self.remote = remote
        self.base = base
        # tuples (local change, remote change)
        self.conflicts = []

    def _merge3(self):
        """Merge the remote project to the local project and store the list of conflicts."""
        self.cache()
        # merge remote into local, with base as common parent
        self.remote._local = self.local
        self.merge_configurations()
        # folders: 1/ to resolve/create the hierarchy
        local_folders = self.merge_folders(self.remote)
        # folders: 2/ delete the local folders which are not in local_folders
        self.clean_folders(local_folders)
        self.merge_file_refs()
        self.merge_properties(self.remote)

    def merge3(self, pathname: str) -> bool:
        """
        Merge the remote project to the local project and save the file.

        Parameters
        ----------
        pathname : str
            Path of the resulting project.
        """
        # report any error as conflict
        try:
            self._merge3()
        except WrongBaseError as e:
            context = (
                'Merge error: Both projects do not share a common ancestor (id "%d")\n'
                % e.project_entity.id
            )
            context += 'Manual merge required'
            self.conflicts.append((context, '-> local <unchanged>', '-> remote <ignored>'))
        except BaseException as e:  # pragma no cover
            # cannot cover unexpected errors
            context = 'Internal merge error: %s\n' % str(e)
            context += 'Manual merge required\n'
            context += traceback.format_exc()
            self.conflicts.append((context, '-> local <unknown>', '-> remote <unknown>'))
        self.save(pathname)
        return len(self.conflicts) == 0

    def merge_configurations(self):
        """Either do nothing, or delete or create a configuration."""
        # save the list of local configurations, remaining items
        # in this list are deleted configurations
        locals = set(self.local.configurations)
        for remote in self.remote.configurations:
            if remote._base:
                # search for corresponding configuration in the local project
                # use base's id since remote can have been suppressed/created again
                local = self.local._map_ids.get(remote._base.id)
                if not local:
                    # search by name
                    local = self.local._map_configurations.get(remote.name)
            else:
                # configuration created in remote, might have been created in local too
                local = self.local._map_configurations.get(remote.name)
            if local:
                # store a reference, useful for creating new properties
                remote._local = local
                locals.remove(local)
                # merge the attributes
                self.merge_attributes(remote, 'name')
            else:
                if not remote._base:
                    # create the local configuration
                    fi.copy_configuration(remote, self.local)
                else:
                    # configuration deleted locally
                    remote._local = None
            assert hasattr(remote, '_local')
        # delete the remaining configurations which are not new
        for local in locals:
            if local._base:
                fi.delete_configuration(local)

    def merge_folders(self, remote_owner: std.ProjectEntity):
        """
        Return the set of local folders with a corresponding remote folder.

        Note: Uses Recursion

        Parameters
        ----------
        remote_owner : ProjectEntity
            Remote owner of the folders to be merged.
        """
        # note: use _map_folders: common attribute for both projects and folders
        locals = set()
        # sort the collection for stable results: dictionaries have a random order with 3.4
        for remote in sorted(remote_owner._map_folders.values(), key=lambda _: _.id):
            # search for corresponding file in the local project
            # use base's id since remote can have been suppressed/created again
            # note: if/else rather than =/if/else for code coverage
            if remote._base:
                local = self.local._map_ids.get(remote._base.id)
            else:
                local = None
            if not local and remote_owner._local:
                # two options:
                # - folder created both remotely and locally
                # - folder suppressed/created again remotely and/or locally
                # search name in remote_owner's local
                local = remote_owner._local._map_folders.get(remote.name)
            if local:
                # store a reference, useful for creating new properties
                # or child elements
                remote._local = local
                locals.add(local)
                # merge the properties
                self.merge_properties(remote)
                # merge the attributes
                self.merge_attributes(remote, 'name', 'extensions', '<owner>')
            else:
                # create the local folder in its container's local
                # the configurations must have been merged first
                if not remote._base:
                    # create the local folder in its owner's local
                    owner_remote = get_element_owner(remote)
                    # note: if/else rather than =/if/else for code coverage
                    if owner_remote._local:
                        owner_local = owner_remote._local
                    else:
                        # target folder does not exist anymore
                        # issue a conflict once the copy is created
                        owner_local = self.local
                    local = fi.copy_folder(remote, owner_local)
                    if not owner_remote._local:
                        context = get_context(local)
                        text_local = '-> local owner = "%s" ("%d")' % (
                            get_name(owner_local),
                            owner_local.id,
                        )
                        text_remote = '-> remote owner = "%s" ("%d") (deleted)' % (
                            get_name(owner_remote),
                            owner_remote.id,
                        )
                        self.conflicts.append((context, text_local, text_remote))
                    locals.add(local)
                else:
                    # folder deleted locally
                    remote._local = None
            # recurse, whenever the folder is deleted locally or not
            locals |= self.merge_folders(remote)
        return locals

    def clean_folders(self, folders: Set[std.Folder]):
        """
        Delete the folders which are not new and were not used in the first pass.

        Parameters
        ----------
        folders : Set[Folder]
            Set of folders present or new in the remote project.
        """
        for local in self.local._folders:
            if local._base and local not in folders:
                # delete the folder
                fi.delete_folder(local)
        pass

    def merge_file_refs(self):
        """Either do nothing, or delete or create a file."""
        # save the list of local files, remaining items
        # in this list are deleted files

        # use cached files, not sure all files can be accessed after having merged the folders
        locals = set(self.local._map_files.values())
        # sort the collection for stable results: dictionaries have a random order with 3.4
        for remote in sorted(self.remote._map_files.values(), key=lambda _: _.id):
            if remote._base:
                # search for corresponding file in the local project
                # use base's id since remote can have been suppressed/created again
                local = self.local._map_ids.get(remote._base.id)
                if not local:
                    # the item might have been suppressed/created again:
                    # search by pathname
                    local = self.local._map_files.get(remote.pathname)
            else:
                # file created in remote, might have been created in local too
                local = self.local._map_files.get(remote.pathname)
            if local:
                # store a reference, useful for creating new properties
                remote._local = local
                locals.remove(local)
                # merge the properties
                self.merge_properties(remote)
                # merge the attributes
                self.merge_attributes(remote, 'persist_as', '<owner>')
            else:
                # create the local file in its container's local
                # the folder hierarchy must have been merged first
                # the configurations must have been merged too
                if not remote._base:
                    # create the local file in its owner's local
                    owner_remote = get_element_owner(remote)
                    # note: if/else rather than =/if/else for code coverage
                    if owner_remote._local:
                        owner_local = owner_remote._local
                    else:
                        # target folder does not exist anymore
                        # issue a conflict once the copy is created
                        owner_local = self.local
                    local = fi.copy_file_ref(remote, owner_local)
                    if not owner_remote._local:
                        context = get_context(local)
                        text_local = '-> local owner = "%s" ("%d")' % (
                            get_name(owner_local),
                            owner_local.id,
                        )
                        text_remote = '-> remote owner = "%s" ("%d") (deleted)' % (
                            get_name(owner_remote),
                            owner_remote.id,
                        )
                        self.conflicts.append((context, text_local, text_remote))
                else:
                    # file deleted locally
                    remote._local = None
        # delete the remaining files which are not new
        for local in locals:
            if local._base:
                # delete the file
                fi.delete_file_ref(local)

    def merge_properties(self, remote_entity: std.Annotable):
        """
        Either do nothing, or delete or create a property.

        Parameters
        ----------
        remote_entity : Annotable
            Remote owner of the properties to be merged.
        """
        assert remote_entity._local
        local_entity = remote_entity._local
        # save the list of local props, remaining items
        # in this list are deleted properties
        locals = set(local_entity.props)
        for remote in remote_entity.props:
            if remote.configuration:
                if not remote.configuration._local:
                    # the configuration has been deleted locally
                    continue
                else:
                    configuration = remote.configuration._local
            else:
                configuration = None
            if remote._base:
                # search for corresponding property in the local project
                # use base's id since remote can have been suppressed/created again
                local = self.local._map_ids.get(remote._base.id)
                if not local:
                    # search by key in the local entity, with the corresponding local configuration
                    key = get_prop_key(remote, configuration)
                    local = local_entity._map_props.get(key)
            else:
                # properties created in remote, might have been created in local too
                key = get_prop_key(remote, configuration)
                local = local_entity._map_props.get(key)
            if local:
                if local in locals:
                    locals.remove(local)
                else:
                    print('Duplicated property %s (%d)' % (local.name, local.id))
                # merge the values
                self.merge_values(local, remote)
            else:
                if not remote._base:
                    # create the local property in its entity's local
                    # the configurations must have been merged first
                    fi.copy_prop(remote, local_entity)
                # else: # property deleted locally
        # delete the remaining properties which are not new
        for local in locals:
            if local._base:
                # delete the property
                fi.delete_prop(local)

    def merge_values(self, local_entity: std.Annotable, remote_entity: std.Annotable):
        """
        Merge the values of both properties.

        Parameters
        ----------
        local_entity : Annotable
            Local owner of the values to be merged.
        remote_entity : Annotable
            Remote owner of the values to be merged.
        """
        # Issue: we don't know which properties are scalar or not, neither if the lists are ordered.
        # -> The lists are considered as not ordered: this may hide conflicts
        # -> The properties having one and only one value are considered as scalar:
        #    this may introduce 'false' conflicts.

        assert (
            not local_entity._base
            or not remote_entity._base
            or local_entity._base == remote_entity._base
        )
        # note: if/else rather than =/if/else for code coverage
        if local_entity._base:
            base_values = local_entity._base.values
        elif remote_entity._base:
            base_values = remote_entity._base.values
        else:
            base_values = None
        local_values = local_entity.values.copy()
        remote_values = remote_entity.values.copy()
        if local_entity.name == '@STUDIO:TOOLCONF':
            # the values are configurations' ids, to be revolved before being merged
            scalar = False
            # remove the configurations deleted locally
            ids = {str(_.id) for _ in self.local.configurations}
            local_values[1:] = [_ for _ in local_entity.values if _ in ids]
            # update the ids of the remote configurations wrt local ones
            ids = {str(_.id): str(_._local.id) for _ in self.remote.configurations if _._local}
            remote_values[1:] = [str(ids.get(_)) for _ in remote_entity.values if _ in ids]
        else:
            scalar = (
                len(local_entity.values) == 1
                and len(remote_entity.values) == 1
                and (not base_values or len(base_values) == 1)
            )
        if scalar:
            local = local_entity.values[0]
            remote = remote_entity.values[0]
            # note: if/else rather than =/if/else for code coverage
            if base_values:
                base = base_values[0]
            else:
                base = None
            if local != remote:
                if local == base:
                    # propagate the change
                    local_entity.values = [remote]
                elif remote != base:
                    # keep the local value and issue a conflict
                    context = get_context(local_entity)
                    text_local = '-> local value = "%s"' % (local if local else '')
                    text_remote = '-> remote value = "%s"' % (remote if remote else '')
                    self.conflicts.append((context, text_local, text_remote))
        else:
            # note: if/else rather than =/if/else for code coverage
            if base_values:
                bases = set(base_values)
            else:
                bases = set()
            locals = set(local_values)
            remotes = set(remote_values)
            # a new value exists only in remotes
            new_values = remotes - bases - locals
            # deleted value exists only in bases and locals
            deleted_values = (bases & locals) - remotes
            # the sets are not ordered, the result below is not stable for unit tests
            # locals = (locals - deleted_values) | new_values
            # local_entity.values = list(locals)
            local_values.extend([_ for _ in remote_values if _ in new_values])
            for value in deleted_values:
                local_values.remove(value)
            local_entity.values = local_values

    def save(self, pathname: str):
        """
        Save the local project as the target project.

        Parameters
        ----------
        pathname : str
            Path of the resulting project.
        """
        # the files provided to merge are stored in the index
        # which means, for default Git configurations, unix format
        # -> the merged file must be in the same format, else
        #    the entire file is marked as changed
        # note: the observed behavior is different when there are
        #       conflicts but not always :(
        crlf = self.is_crlf()

        # save the local project as pathname
        tmp = pathname + '.etp'
        self.local.save(tmp)
        if self.conflicts:
            # append the conflicts to the end of file
            path = Path(tmp)
            with path.open('at') as f:
                for context, local, remote in self.conflicts:
                    # path not meaningful, at least with Git
                    # f.write('<<<<<<< HEAD:%s\n' % path.name)
                    f.write('<<<<<<< HEAD\n')
                    f.write('%s\n' % context)
                    f.write('%s\n' % local)
                    f.write('=======\n')
                    f.write('%s\n' % remote)
                    # f.write('>>>>>>> remote:%s\n' % path.name)
                    f.write('>>>>>>>\n')
        if not crlf:
            path = Path(tmp)
            with path.open('r') as f:
                content = f.read()
            bytes = content.encode('utf-8')
            with path.open('wb') as f:
                f.write(bytes)
        os.replace(tmp, pathname)

    def is_crlf(self) -> bool:
        """Detect the mode of the local file, either unix (LF) or windows (CR/LF)."""
        with open(self.local.pathname, 'rb') as f:
            content = f.read()
        crlf = content.count(b'\r\n')
        return crlf > 0

    def cache(self):
        """Cache additional relationships and attributes prior to the merge."""
        for project in self.base, self.local, self.remote:
            CacheMaps().visit(project)
        for project in self.local, self.remote:
            CacheBase(self.base).visit(project)

    def merge_attributes(self, remote: std.ProjectEntity, *attributes: str):
        """
        Propagate the attributes.

        Parameters
        ----------
        remote_entity : ProjectEntity
            Remote entity which attributes should me merged.
        """
        local = remote._local
        base = remote._base
        # assert local._base == base
        texts_local = []
        texts_remote = []
        for attribute in attributes:
            if attribute == '<owner>':
                # ownership requires a dedicated code
                local_owner = get_element_owner(local)
                remote_owner = get_element_owner(remote)
                local_remote_owner = remote_owner._local
                if local_remote_owner != local_owner:
                    if not self.is_moved(local):
                        if local_remote_owner:
                            # propagate the move
                            fi.move_element(local, local_remote_owner)
                        else:
                            # target folder does not exist anymore
                            # issue a conflict
                            texts_local.append(
                                '-> local owner = "%s" ("%d")'
                                % (get_name(local_owner), local_owner.id)
                            )
                            texts_remote.append(
                                '-> remote owner = "%s" ("%d") (deleted)'
                                % (get_name(remote_owner), remote_owner.id)
                            )
                    elif self.is_moved(remote):
                        # keep the local ownership and issue a conflict
                        texts_local.append(
                            '-> local owner = "%s" ("%d")' % (get_name(local_owner), local_owner.id)
                        )
                        texts_remote.append(
                            '-> remote owner = "%s" ("%d")'
                            % (get_name(local_remote_owner), local_remote_owner.id)
                        )
            else:
                # note: if/else rather than =/if/else for code coverage
                if base:
                    base_value = getattr(base, attribute)
                else:
                    base_value = None
                local_value = getattr(local, attribute)
                remote_value = getattr(remote, attribute)
                if remote_value != local_value:
                    if base and local_value == base_value:
                        # propagate the change
                        setattr(local, attribute, remote_value)
                    elif not base or remote_value != base_value:
                        # keep the local value and issue a conflict
                        texts_local.append('-> local %s = "%s"' % (attribute, local_value))
                        texts_remote.append('-> remote %s = "%s"' % (attribute, remote_value))
        if texts_local or texts_remote:
            context = get_context(local)
            self.conflicts.append((context, '\n'.join(texts_local), '\n'.join(texts_remote)))

    def is_moved(self, element: std.Element) -> bool:
        """
        Return whether an object has a different owner from its base object.

        * An element, local or remote, is moved when its owner's base is different from
          its base's owner.
        * An element is considered as moved if one of the bases is None.

        Parameters
        ----------
        element : Element
            Input element.

        Returns
        -------
        bool
            `True` if the element has been moved to a different owner.
        """
        owner = get_element_owner(element)
        if not element._base or not owner._base:
            return True
        return get_element_owner(element._base) != owner._base
