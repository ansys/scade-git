# Copyright (C) 2021 - 2024 ANSYS, Inc. and/or its affiliates.
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

"""Merge3 for SCADE ALMGW not exported traceability files (ALMGT)."""

from lxml import etree as et


class LLR:
    """
    Wrapper for `<object>` XML element.

    This corresponds to a Scade model element.

    Parameters
    ----------
    id : str
        Oid of the model element.
    path : str
        Scade path of the model element.
    """

    def __init__(self, id: str = '', path: str = ''):
        self.elem = None
        self.id = id
        self.path = path
        # traceability edits: either add or remove link to hlr
        self.edits = {}

    def is_empty(self) -> bool:
        """Return whether the instance contains traceability links."""
        return len(self.edits) == 0

    def parse(self, elem: et._Element):
        """
        Wrap an `<object>` XML element and cache its attributes.

        Cache the sub-elements `<requirement>` in a dictionary.

        Parameters
        ----------
        elem : et._Element
            Wrapped XML element.
        """
        self.elem = elem
        self.id = self.elem.get('id')
        self.path = self.elem.get('pathName', '')
        for elem in self.elem.findall('requirement'):
            req = elem.get('id')
            self.edits[req] = elem
        return self

    def create_elem(self, parent: et._Element):
        """
        Create the underlying XML element.

        Parameters
        ----------
        parent : et._Element
            Containing XML element.
        """
        self.elem = et.SubElement(parent, 'object', id=self.id, pathName=self.path)
        return self


class GTFile:
    """Wrapper for ALMGW not exported traceability files (ALMGT)."""

    def __init__(self):
        self.tree = None
        self.llrs = {}

    def parse(self, filename: str):
        """
        Parse the file and cache the elements in dictionaries.

        Parameters
        ----------
        filename : str
            Input filename.
        """
        parser = et.XMLParser(remove_blank_text=True)
        try:
            self.tree = et.parse(filename, parser)
        except OSError as e:
            print(e)
            return None
        for elem in self.tree.getroot().findall('object'):
            llr = LLR().parse(elem)
            self.llrs[llr.id] = llr
        return self

    def save(self, filename: str):
        """
        Save the modified file.

        Parameters
        ----------
        filename : str
            Input filename.
        """
        et.indent(self.tree.getroot(), space='    ')
        self.tree.write(
            filename, encoding='utf-8', standalone='yes', xml_declaration=True, pretty_print=True
        )

    def merge(self, other: 'GTFile', base: 'GTFile') -> bool:
        """
        Merge the remote file, based on a common ancestor.

        Parameters
        ----------
        other : GTFile
            File to merge to the current instance.
        base : GTFile
            Common ancestor file.
        """
        # self += other - base
        for otherllr in other.llrs.values():
            selfllr = self.llrs.get(otherllr.id)
            basellr = base.llrs.get(otherllr.id)
            if basellr:
                # remove the edits present in base
                to_remove = [_ for _ in otherllr.edits.keys() if _ in basellr.edits]
                for hlr in to_remove:
                    basellr.edits.pop(hlr)
                    otherllr.edits.pop(hlr)
            # add remaining remote hlrs to local ones
            if not selfllr and not otherllr.is_empty():
                # create an instance
                selfllr = LLR(otherllr.id, otherllr.path)
                # and add it ti the file
                selfllr.create_elem(self.tree.getroot())

            for hlr, elem in otherllr.edits.items():
                if hlr not in selfllr.edits:
                    # add the hlr edit
                    et.SubElement(
                        selfllr.elem, 'requirement', id=hlr, traceType=elem.get('traceType')
                    )

        # the remaining hlrs in base have been deleted on remote:
        # remove them locally if still present
        for basellr in base.llrs.values():
            selfllr = self.llrs.get(basellr.id)
            if selfllr:
                for hlr in basellr.edits.keys():
                    elem = selfllr.edits.pop(hlr, None)
                    if elem is not None:
                        print('not empty')
                        selfllr.elem.remove(elem)
                if selfllr.is_empty():
                    self.llrs.pop(selfllr.id)
                    self.tree.getroot().remove(selfllr.elem)

        # the semantics of the file prevent any conflict
        return True


def merge3(local: str, remote: str, base: str, merged: str) -> bool:
    """
    Merge `remote` and `local` into `merged`.

    Parameters
    ----------
    local : str
        Path of the local file.
    remote : str
        Path of the file to merge.
    base : str
        Path of the common anecestor.
    merged : str
        Path of the result file.
    """
    gtbase = GTFile().parse(base)
    gtremote = GTFile().parse(remote)
    gtlocal = GTFile().parse(local)
    if not gtbase or not gtremote or not gtlocal:
        # error already reported
        status = False
    else:
        status = gtlocal.merge(gtremote, gtbase)
    if status:
        gtlocal.save(merged)
    return status
