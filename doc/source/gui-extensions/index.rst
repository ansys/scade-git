GUI Extensions
==============

Purpose
-------
This is a demonstrator for Git support in SCADE.

It adds Git commands to the SCADE IDE.

Features
--------

The Git extension supports several commands:

* Refresh: Update the Git status of all project files.

  Note: You must save the SCADE project before so that Git detects changes.

* Stage selected files or all unstaged files: Add files to the Git staging area.
* Unstage selected files or all staged files: Remove files from the Git staging area.
* Reset All: Discard all changes and reset the Git repository to the last commit of the current branch.
* Commit: Commit files in the staging area.
* Diff: Select a version of the project and copy it to a temporary folder in order to launch the SCADE Diff Merge tool.

Git Browser
~~~~~~~~~~~

It lists the Git status for each files of the SCADE project.
The update (Refresh command) is not automatic and must be done after each save of the project.

The name of the top-level folder mentions the current branch.

.. figure:: /_static/Gittab.png

Git Menu
~~~~~~~~

All actions described above are available in a Git menu or in the Git toolbar:

.. figure:: /_static/Gitmenu.png

Actions on selected files are available in a Git contextual menu:

.. figure:: /_static/Gittabcontext.png

Git Commit
~~~~~~~~~~

An edit box allows to enter the commit message:

.. figure:: /_static/Gitcommit.png

Git Diff Merge
~~~~~~~~~~~~~~

A dialog lists all available branches in Git.

.. figure:: /_static/Gitdiff.png

Once you select one branch and click on Diff, the extension copies this project
version in a temporary folder and lists the path in the Git messages window.
You must add this project to the workspace and manually launch the
Diff Analyzer to start a diff merge session.
There is no script access to this IDE command at this time to completely
automate the process.

.. figure:: /_static/Gitdifflog.png

The temporary folder must be manually cleaned (TBD: add an action to clean it from the IDE).
It is located in ``%LOCALAPPDATA%\temp\SCADE\git-diff\<git repository name>\<branch name (only alpha num char, no spaces)>``

..
    ## Installation

    ### Ansys SCADE Packages Manager
    Refer to the [Ansys SCADE Packages Manager](https://niclineseg.ansys.com/eseg/packages-manager) documentation on how to install a SCADE extension.

    ### Manual install
    Go to ``https://niclineseg.ansys.com/groups/eseg/-/packages``, click on the latest ansys-scade-packagesmanager version and on the new page download the \*.whl file under the Files section at bottom and place it in a local folder.

    Then use the command:
    ```console
    "C:\Program Files\ANSYS Inc\<SCADE version>\SCADE\contrib\<Python version>\python.exe" -m pip install ansys-scade-packagesmanager --user --find-links=<path of the folder where you downloaded the whl file>
    ```
    There is a specific Python version for each SCADE Version.
    | SCADE Versions | Python Versions |
    |----------------|-----------------|
    | -> v194        | Python34        |
    | v201 -> v231   | Python37        |
    | v232 ->        | Python310       |

    Packages are installed to the Python user install directory (--user): %APPDATA%\Python\<Python version>

    It means that a package installed with Python37 is available for all SCADE versions using this Python version. There is no need to install a SCADE package for each SCADE version.

    ### Post Installation (manual install)

    The SCADE package must be registered as a SCADE extension. Run the registration script installed with the package:
    ```console
    %APPDATA%\Python\<Python version>\Scripts\register_ansys_scade_gitextension
    ```

    The script also automatically configures git with:
    * register the etpmerge custom merge driver in Git global settings
    ```console
    git config --global merge.etpmerge.name "Merge for SCADE project files"
    git config --global merge.etpmerge.driver "\"%APPDATA%\Python\Python%PYTHON_VERSION%\Scripts\etpmerge.exe\" -b %O -l %A -r %B -m %A"
    git config --global merge.etpmerge.trustexitcode "true"
    ```

    * register no diff for xscade files
    ```console
    git config --global merge.xscademerge.name "Merge for SCADE model files"
    git config --global merge.xscademerge.driver "exit 1"
    git config --global merge.xscademerge.trustexitcode "true"
    ```

    * configure global .gitattributes use etpmerge & xscademerge for all etp & xscade files
    %USERPROFILE%\.config\git\attributes
    ```console
    *.etp merge=etpmerge"
    *.xscade merge=xscademerge"
    ```
