GUI extensions
==============

Purpose
-------
This is a demonstrator for Git support in SCADE.

It adds Git commands to the SCADE IDE.

Features
--------

The Git extension supports several commands:

* Refresh: Update the Git status of all project files.

  Note: You must save the SCADE project before so that Git can detect changes.

* Stage selected files or all unstaged files: Add files to the Git staging area.
* Unstage selected files or all staged files: Remove files from the Git staging area.
* Reset All: Discard all changes and reset the Git repository to the last commit of the current branch.
* Commit: Commit files in the staging area.
* Diff: Select a version of the project and copy it to a temporary folder to launch the SCADE Diff Merge tool.

Git browser
~~~~~~~~~~~

It lists the Git status for each file of the SCADE project.
The update (Refresh command) is not automatic and must be done after each save of the project.

The name of the top-level folder mentions the current branch.

.. image:: /_static/Gittab.png
 :alt: Git browser

Git menu
~~~~~~~~

All preceding actions are available in a Git menu or in the Git toolbar:

.. image:: /_static/Gitmenu.png
  :alt: Git menu

Actions on selected files are available in a Git contextual menu:

.. image:: /_static/Gittabcontext.png
  :alt: Git contextual  menu

Git commit
~~~~~~~~~~

An edit box allows to enter the commit message:

.. image:: /_static/Gitcommit.png
  :alt: Git commit message

Git diff merge
~~~~~~~~~~~~~~

A dialog lists all available branches in Git.

.. image:: /_static/Gitdiff.png
  :alt: Git branches

Once you select one branch and click Diff, the extension copies this project
version in a temporary folder and lists the path in the Git messages window.
You must add this project to the workspace and manually launch the
Diff Analyzer to start a diff merge session.
There is no script access to this IDE command at this time to completely
automate the process.

.. image:: /_static/Gitdifflog.png
  :alt: Git diff log message

The temporary folder must be manually cleaned if you need to free disk space.
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
