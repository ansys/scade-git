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

"""Checks the absence of duplicate ids in a project."""

from argparse import ArgumentParser

from ansys.scade.apitools import declare_project

# isort: split

import scade.model.project.stdproject as std
from scade.model.project.stdproject import get_roots as get_projects

from .visitor import Visit


class CheckIds(Visit):
    """Visitor for checking duplicated ids."""

    def __init__(self):
        """Declare global maps, to be accessed from any elements."""
        self.map_ids = {}

    def visit_project_entity(self, project_entity: std.ProjectEntity):
        """
        Register the entity's id if not already present, otherwise report the issue.

        Parameters
        ----------
        project_entity : std.ProjectEntity
            Visited project entity.
        """
        if project_entity.id in self.map_ids:
            print('%d: duplicated id' % project_entity.id)
        else:
            self.map_ids[project_entity.id] = project_entity
        super().visit_project_entity(project_entity)


def main():
    """Entry point."""
    parser = ArgumentParser(description='Check SCADE project files ids')
    parser.add_argument('-p', '--project', metavar='<project>', help='project file', required=True)
    options = parser.parse_args()

    declare_project(options.project)
    # load the declared projects
    project = get_projects()[0]

    CheckIds().visit(project)


if __name__ == '__main__':
    main()
