# Advanced: Test Notes
## Goals
This test suite is used to ensure the folders are properly merged/reconciled after changes in the hierarchy combined to deletion/creation operations.

## Folders and Files
The name of the elements describe the change performed in both local and remote projects.

## Notes
There are some conflicts the current design can't report easily. The following elements are suppressed from the merged project although they are present in both local and remote projects:
* Source/dd source to delete remote (local)
* Source/dd source to delete remote (local).txt
These two elements have been moved locally to a folder which is deleted remotely.
For the symmetric use case, a conflict is issued because we have to move the following items to a folder which no longer exists:
* Source/dd source to delete local (remote)
* Source/dd source to delete local (remote).txt
