# Crlf: Test Notes
## Goals
This test suite is used to ensure the line endings of the merged project are preserved.

Indeed, the merge tools uses files located in the index, before the line endings are normalized with respect to the host, Windows.
The SCADE APi saves files with CRLF, which makes the file changed 100%, when there are no conflicts. If a conflict occurs, the file is in the working area, ang Git normalizes the line endings.

## Project Files
The project files are declared with the attribute `-text` to prevent Git to perform line endings normalization.
