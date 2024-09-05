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

"""SCADE IDE abstraction."""

from abc import ABCMeta, abstractmethod
from typing import Any, List


class Ide(metaclass=ABCMeta):
    """SCADE IDE abstraction."""

    @abstractmethod
    def create_browser(self, name: str, icon: str = ''):
        """Abstract scade.create_browser."""
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def browser_report(
        self,
        item: Any,
        parent: Any = None,
        expanded: bool = False,
        name: str = '',
        icon_file: str = '',
    ):
        """Abstract scade.browser_report."""
        raise NotImplementedError('Abstract method call')

    @property
    @abstractmethod
    def selection(self) -> List[Any]:
        """Abstract scade.selection."""
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def get_active_project(self) -> Any:
        """Abstract scade.active_project."""
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def get_projects(self) -> List[Any]:
        """Abstract scade.model.project.stdproject.get_roots."""
        raise NotImplementedError('Abstract method call')

    @abstractmethod
    def log(self, text: str):
        """Abstract scade.tabput."""
        raise NotImplementedError('Abstract method call')


try:
    from scade.tool.suite.gui.commands import Command as _Command
except ImportError:
    import scade

    scade.output('fake activated\n')

    class _Command:
        """Stub for scade.tool.suite.gui.commands.Command."""

        def __init__(
            self,
            name: str,
            status_message: str,
            tooltip_message: str,
            image_file: str = None,
        ):
            self.name = name
            self.status_message = status_message
            self.tooltip_message = tooltip_message
            self.image_file = image_file

        def on_enable(self) -> bool:
            """Return whether the command can be activated, `True` by default."""
            return True


class Command(_Command):
    """Base class for commands."""

    def __init__(self, ide: Ide, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ide = ide
