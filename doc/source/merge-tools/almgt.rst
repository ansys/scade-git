ALM Gateway files for non-exported traceability links
=====================================================

Overview
--------

The ALM Gateway files (ALMGT) about non-exported traceability links are temporary XML
files that store traceability edits not yet exported to an ALM tool.

They are usually not tracked in version control systems, but there may exist
some use cases where this is required. The XML syntax does not allow automatic
merging: The ``almgtmerge`` utility merges two ALMGT files derived from a
common ancestor.

Conflict resolution
-------------------

N/A: The semantics of ALMGT files prevents any conflict when merging two files.
