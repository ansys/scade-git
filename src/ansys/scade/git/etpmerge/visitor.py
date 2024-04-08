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

"""Visitor for SCADE project files."""

import scade.model.project.stdproject as std


class Visit:
    """Base class for visiting SCADE project files."""

    def visit(self, project_entity: std.ProjectEntity):
        """Entry point of the visit."""
        eval("self.%s(project_entity)" % _map_visit_functions[type(project_entity)])

    def visit_annotable(self, annotable: std.Annotable):
        """Visit function for Annotable."""
        self.visit_project_entity(annotable)
        for prop in annotable.props:
            self.visit(prop)

    def visit_configuration(self, configuration: std.Configuration):
        """Visit function for Configuration."""
        self.visit_project_entity(configuration)

    def visit_element(self, element: std.Element):
        """Visit function for Element."""
        self.visit_annotable(element)

    def visit_file_ref(self, file_ref: std.FileRef):
        """Visit function for FileRef."""
        self.visit_element(file_ref)

    def visit_folder(self, folder: std.Folder):
        """Visit function for Folder."""
        self.visit_element(folder)
        for element in folder.elements:
            self.visit(element)

    def visit_project(self, project: std.Project):
        """Visit function for Project."""
        self.visit_annotable(project)
        for configuration in project.configurations:
            self.visit(configuration)
        for root in project.roots:
            self.visit(root)

    def visit_project_entity(self, project_entity: std.ProjectEntity):
        """Visit function for ProjectEntity."""
        pass

    def visit_prop(self, prop: std.Prop):
        """Visit function for Prop."""
        self.visit_project_entity(prop)


_map_visit_functions = {
    std.Configuration: 'visit_configuration',
    std.FileRef: 'visit_file_ref',
    std.Folder: 'visit_folder',
    std.Project: 'visit_project',
    std.Prop: 'visit_prop',
}
