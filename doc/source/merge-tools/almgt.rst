ALM Gateway not Exported Traceability File
==========================================

Overview
--------

The ALM Gateway not exported traceability files (ALMGT) are temporary XML
files that store traceability edits not yet exported to an AML tool.

They are usually not tracked in version control systems, but there may exist
some use cases where this is required. The XML syntax does not allow automatic
merging: The ``almgtmerge`` utility merges two AMLGT files derived from a
common ancestor.

Conflict Resolution
-------------------

N/A: The semantics of AMLGT files prevent any conflict when merging two files.
