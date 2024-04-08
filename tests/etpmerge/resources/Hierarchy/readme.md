# Hierarchy: Test Notes
## Goals
This test suite is used to ensure the folders are properly merged/reconciled after changes in the hierarchy.

It does not consider the use cases which have their own test suites, for example:
* Changes combining drag and drop, creation and deletion.

## Folders
The name of the folders describe the change performed in both local and remote projects.
Each moved folder gets a new child, to have test a minima the correctness of the propagation.
