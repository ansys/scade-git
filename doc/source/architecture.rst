Architecture
============

Overview
--------

The Ansys SCADE Git Extensions package provides a comprehensive integration between
Ansys SCADE Suite and Git version control. The architecture is composed of three main
components that work together to enable Git operations within the SCADE IDE and provide
specialized merge tools for SCADE-specific file formats.

System Architecture
-------------------

The following diagram illustrates the overall architecture of the SCADE Git Extensions:

.. mermaid::
   :caption: SCADE Git Extensions Architecture
   :align: center

   graph TB
       subgraph IDE["SCADE Suite IDE"]
           GUI["GUI Extension<br/>(gitextension.py)<br/>• Menus, Toolbars, Context Menus<br/>• Git Browser UI<br/>• Dialogs (Commit, Diff, Reset)"]
           CORE["Extension Core<br/>(gitextcore.py)<br/>• Command Handlers<br/>• Browser Management<br/>• File Status Tracking"]
           IDEINTF["IDE Interface<br/>(ide.py)<br/>• Abstract IDE operations<br/>• Studio implementation"]

           GUI --> CORE
           CORE --> IDEINTF
       end

       GITCLIENT["Git Client<br/>(gitclient.py)<br/>• Dulwich wrapper<br/>• Repository operations<br/>• Status management"]
       SCADEAPI["SCADE API<br/>• Project API<br/>• Model API"]

       IDEINTF --> GITCLIENT
       IDEINTF --> SCADEAPI

       DULWICH["Dulwich Library<br/>• Pure Python Git impl<br/>• Repository access<br/>• Porcelain commands"]
       GITREPO["Git Repository<br/>• .git directory<br/>• Working tree<br/>• Index/staging area"]

       GITCLIENT --> DULWICH
       DULWICH --> GITREPO

       subgraph MERGE["Command-Line Merge Tools"]
           ETPMERGE["ETP Merge<br/>(etpmerge/)<br/>• etpmerge3.py<br/>• cache.py<br/>• visitor.py<br/>• fi.py (FileInfo)<br/>• utils.py<br/><br/>Merges SCADE project<br/>files (.etp)"]
           ALMGTMERGE["ALMGT Merge<br/>(almgtmerge/)<br/>• almgtmerge3.py<br/><br/>Merges SCADE ALMGW<br/>traceability files (.almgt)"]
       end

       GITINVOKE["Git merge drivers<br/>(configured via .gitattributes)"]

       GITREPO -.-> GITINVOKE
       GITINVOKE -.-> ETPMERGE
       GITINVOKE -.-> ALMGTMERGE
       ETPMERGE -.-> SCADEAPI

       style IDE fill:#e1e1e1,stroke:#666,stroke-width:2px
       style MERGE fill:#e1e1e1,stroke:#666,stroke-width:2px
       style GUI fill:#add8e6,stroke:#333
       style CORE fill:#add8e6,stroke:#333
       style IDEINTF fill:#add8e6,stroke:#333
       style GITCLIENT fill:#ffffcc,stroke:#333
       style DULWICH fill:#ffffcc,stroke:#333
       style GITREPO fill:#ffffcc,stroke:#333
       style SCADEAPI fill:#90ee90,stroke:#333
       style ETPMERGE fill:#f08080,stroke:#333
       style ALMGTMERGE fill:#f08080,stroke:#333
       style GITINVOKE fill:#ffffff,stroke:#333


Component Description
---------------------

GUI Extension Layer
~~~~~~~~~~~~~~~~~~~

**Location:** ``src/ansys/scade/git/extension/``

The GUI extension integrates directly with the SCADE Suite IDE through the SCADE Python API.
It consists of the following key components:

* **gitextension.py**: Main entry point for the SCADE IDE extension

  - Implements ``Studio`` class that provides SCADE IDE-specific functionality
  - Creates Git browser, menus, toolbars, and context menus
  - Handles user interactions and delegates to command handlers
  - Implements ``GitClient`` subclass for IDE-specific logging

* **gitextcore.py**: Core command implementations

  - ``CmdRefresh``: Updates Git status for all project files
  - ``CmdStage`` / ``CmdStageAll``: Stages files for commit
  - ``CmdUnstage`` / ``CmdUnstageAll``: Unstages files
  - ``CmdCommit``: Commits staged changes with a message
  - ``CmdReset``: Resets repository to last commit
  - ``CmdDiff``: Exports a branch to temporary folder for diff/merge
  - Manages the Git browser UI with status categories:

    - Staged files
    - Unstaged files
    - Clean files
    - External files

* **ide.py**: Abstract interface layer

  - Defines ``Ide`` abstract base class for IDE operations
  - Defines ``Command`` abstract base class for commands
  - Allows potential support for other IDEs in the future

Git Client Layer
~~~~~~~~~~~~~~~~

**Location:** ``src/ansys/scade/git/extension/gitclient.py``

The Git client provides a Python interface to Git operations using the Dulwich library:

* **GitClient class**: Wraps Dulwich for Git operations

  - Repository discovery (``find_git_repo()``)
  - File status tracking (``get_file_status()``)
  - Staging operations (``stage()``, ``unstage()``)
  - Commit operations (``commit()``)
  - Branch management (``get_branches()``)
  - Diff operations (``checkout_to_dir()``)
  - Uses Dulwich (pure Python Git implementation) for platform independence

* **GitStatus enum**: Defines file status states

  - ``added``: File added to index
  - ``modified_staged``: Modified and staged
  - ``modified_unstaged``: Modified but not staged
  - ``removed_staged``: Deleted and staged
  - ``removed_unstaged``: Deleted but not staged
  - ``untracked``: Not tracked by Git
  - ``clean``: No changes
  - ``extern``: Outside repository
  - ``error``: Error state
  - ``none``: Unknown state

Technology Choice: **Dulwich**

The package uses Dulwich instead of GitPython or direct command-line invocation because:

- Pure Python implementation (no Git binary required)
- Cross-platform compatibility
- Programmatic access to Git internals
- Version >= 0.21.3 required

Merge Tools
~~~~~~~~~~~

**Location:** ``src/ansys/scade/git/almgtmerge/`` and ``src/ansys/scade/git/etpmerge/``

The merge tools implement three-way merge algorithms for SCADE-specific file formats:

ETP Merge (Project Files)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Handles SCADE project files (``.etp``):

* **etpmerge3.py**: Main merge logic using SCADE Project API

  - ``EtpMerge3`` class performs semantic merge of project structures
  - Handles configurations, file references, tools, properties
  - Detects and reports conflicts (duplicate IDs, incompatible changes)
  - Preserves project structure and relationships

* **cache.py**: Caching mechanism for project elements

  - ``CacheBase``: Base class for element caching
  - ``CacheMaps``: Maps for quick lookup by ID and path
  - Optimizes merge performance for large projects

* **visitor.py**: Project tree traversal

  - Implements visitor pattern for project elements
  - Collects all elements for comparison

* **fi.py**: File information management

  - Tracks file references and their attributes
  - Manages relative/absolute path conversions

* **utils.py**: Helper utilities for element comparison

ALMGT Merge (Traceability Files)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Handles SCADE ALMGW traceability files (``.almgt``):

* **almgtmerge3.py**: XML-based merge for requirements traceability

  - Uses ``lxml`` for XML parsing and manipulation
  - Merges traceability links between requirements (HLR) and model elements (LLR)
  - ``LLR`` class: Represents a model element with traceability links
  - Detects conflicting edits to the same traceability link
  - Preserves XML structure and attributes

Merge Tool Interface
^^^^^^^^^^^^^^^^^^^^

Both tools expose a command-line interface compatible with Git merge drivers:

.. code-block:: bash

    python -m ansys.scade.git.etpmerge -l <local> -r <remote> -b <base> -m <merged>
    python -m ansys.scade.git.almgtmerge -l <local> -r <remote> -b <base> -m <merged>

Parameters:
  - ``-l/--local``: Current branch version (LOCAL)
  - ``-r/--remote``: Incoming branch version (REMOTE)
  - ``-b/--base``: Common ancestor version (BASE)
  - ``-m/--merged``: Output file (MERGED)

The tools return:
  - Exit code 0: Successful merge (no conflicts)
  - Exit code 1: Merge conflicts detected
  - Exit code >1: Error condition

Registration and Configuration
-------------------------------

Package Registration
~~~~~~~~~~~~~~~~~~~~

**Location:** ``src/ansys/scade/git/register.py`` and ``unregister.py``

The package provides registration scripts to configure Git for SCADE files:

* Registers custom merge drivers in Git configuration
* Configures ``.gitattributes`` for automatic tool invocation
* Sets up SCADE IDE extension registration

SCADE IDE Integration
~~~~~~~~~~~~~~~~~~~~~~

**Location:** ``src/ansys/scade/git/*.srg``

The package includes SCADE Studio registry files (``.srg``):

* **git.srg**: Main registry file (SCADE 2025 R1+)
* **git-37.srg**: Python 3.7 specific (SCADE 2021 R2 - 2023 R1)
* **git-310.srg**: Python 3.10 specific (SCADE 2023 R2+)

These files register the extension with SCADE Suite IDE, enabling:
- Git menu and toolbar
- Git browser panel
- Context menu actions
- Command handlers

Registration Mechanism
^^^^^^^^^^^^^^^^^^^^^^

SCADE 2025 R1 and later use the ``ansys.scade.registry`` entry point defined in
``pyproject.toml``. Earlier versions require explicit ``.srg`` file placement in
``%APPDATA%\Scade\Customize``.

The ``srg()`` function in ``__init__.py`` implements the entry point, returning the
path to the appropriate registry file based on Python version.

Data Flow
---------

Git Status Refresh
~~~~~~~~~~~~~~~~~~

1. User clicks "Refresh" in IDE
2. ``CmdRefresh`` executed via ``gitextcore.py``
3. Saves active SCADE project
4. ``GitClient.refresh()`` locates Git repository
5. ``GitClient`` iterates through project files
6. For each file: ``get_file_status()`` queries Git index/working tree
7. File status determined via Dulwich API
8. ``refresh_browser()`` updates Git browser UI
9. Files categorized into: Staged, Unstaged, Clean, External

Stage and Commit
~~~~~~~~~~~~~~~~

1. User selects files in browser or uses "Stage All"
2. ``CmdStage`` or ``CmdStageAll`` executed
3. ``GitClient.stage()`` called with file paths
4. Dulwich updates Git index
5. Browser refreshed to show new status
6. User enters commit message in dialog
7. ``CmdCommit`` executed
8. ``GitClient.commit()`` creates commit object
9. Dulwich writes commit to repository
10. Browser refreshed

Diff/Merge Workflow
~~~~~~~~~~~~~~~~~~~

1. User selects "Diff" command
2. ``CmdDiff`` displays branch selection dialog
3. User selects target branch
4. ``GitClient.checkout_to_dir()`` exports branch to temporary folder
5. Path logged to IDE messages window
6. User manually adds exported project to workspace
7. User launches SCADE Diff Analyzer
8. Manual merge performed using SCADE tools

Automated Merge (Git Merge)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. User performs ``git merge`` command
2. Git detects conflict in ``.etp`` or ``.almgt`` file
3. ``.gitattributes`` specifies custom merge driver
4. Git invokes ``python -m ansys.scade.git.etpmerge`` (or almgtmerge)
5. Merge tool reads BASE, LOCAL, REMOTE files
6. Semantic merge performed using SCADE APIs
7. MERGED file written with resolved changes
8. Conflicts reported to stderr
9. Exit code indicates success/conflict/error
10. Git marks file as resolved or conflicted

File Status Determination
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``GitClient.get_file_status()`` method determines file status through:

1. Check if file exists in filesystem
2. Check if file is tracked in Git repository
3. Compare file hash with Git index
4. Check if file is staged (in Git index)
5. Determine file status based on:

   - Not in repo and not in filesystem → ``error``
   - Not in repo → ``untracked``
   - Outside repo → ``extern``
   - In index different from HEAD → ``added``, ``modified_staged``, ``removed_staged``
   - In working tree different from index → ``modified_unstaged``, ``removed_unstaged``
   - Otherwise → ``clean``

Security Considerations
-----------------------

Path Traversal Protection
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``badpath()`` and ``badlink()`` functions in ``gitextcore.py`` protect against
path traversal attacks when extracting tarballs for diff operations:

- Validates that extracted paths remain within intended base directory
- Checks both direct paths and symbolic links
- Prevents malicious archives from writing outside temporary directories

Dependency Management
~~~~~~~~~~~~~~~~~~~~~

The package uses ``site.getusersitepackages()`` to ensure user-installed modules
take precedence over system Python installations, allowing users to upgrade
dependencies like Dulwich without admin privileges.

Extension Points
----------------

The architecture supports extension through:

1. **Multiple IDEs**: The abstract ``Ide`` class allows implementing support for
   other SCADE environments or IDEs beyond SCADE Suite.

2. **Additional Merge Tools**: New merge tools can be added for other SCADE file
   formats by following the established interface pattern.

3. **Custom Commands**: New Git commands can be added by implementing the ``Command``
   abstract class and registering them in the extension.

4. **Alternative Git Backends**: While Dulwich is currently used, the ``GitClient``
   abstraction allows switching to other Git implementations if needed.

Design Rationale
----------------

Separation of Concerns
~~~~~~~~~~~~~~~~~~~~~~

The architecture separates:

- **UI layer** (gitextension.py): IDE-specific interactions
- **Command layer** (gitextcore.py): Business logic
- **Client layer** (gitclient.py): Git operations
- **Merge tools**: Independent command-line utilities

This separation enables:
  - Testing without IDE
  - Reuse of merge tools in different contexts
  - Clear boundaries between components

Pure Python Implementation
~~~~~~~~~~~~~~~~~~~~~~~~~~

Using Dulwich provides:
  - No dependency on Git binary installation
  - Cross-platform compatibility (Windows, Linux, macOS)
  - Programmatic access to Git internals
  - Easier debugging and error handling

Semantic Merge Approach
~~~~~~~~~~~~~~~~~~~~~~~~

Instead of line-based textual merge, the ETP and ALMGT merge tools:
  - Parse files into semantic structures (using SCADE API and lxml)
  - Merge at the element level (projects, configurations, traceability links)
  - Preserve semantic validity of SCADE files
  - Detect semantic conflicts (for example: duplicate element IDs)

This prevents corruption of binary-like or structured XML files that
textual merge would produce.

Limitations and Future Enhancements
-----------------------------------

Current Limitations
~~~~~~~~~~~~~~~~~~~

1. **Manual Diff Launch**: The Diff command exports to a temporary folder, but
   the user must manually launch the SCADE Diff Analyzer due to lack of script
   access to this IDE command.

2. **No Auto-Refresh**: The Git browser does not automatically refresh on file
   changes; users must save the project and click Refresh.

3. **Single Repository**: The extension assumes one Git repository per SCADE
   project workspace.

4. **Limited History**: No GUI access to Git history, blame, or log visualization.

Potential Enhancements
~~~~~~~~~~~~~~~~~~~~~~

1. **File System Watcher**: Automatically refresh Git status on file changes
2. **History Browser**: Display commit history, branches, and tags in the IDE
3. **Visual Diff**: Integrate SCADE Diff Analyzer directly into the IDE
4. **Pull/Push Support**: Add remote repository operations
5. **Branch Management**: Create, delete, merge branches from IDE
6. **Conflict Resolution UI**: Visual tool for resolving merge conflicts
7. **Additional Merge Tools**: Support for more SCADE file formats (.xscade, .ann)

Conclusion
----------

The Ansys SCADE Git Extensions architecture provides a robust, modular integration
between SCADE Suite and Git version control. By separating concerns across layers,
using pure Python implementations, and providing semantic merge capabilities for
SCADE-specific file formats, the package enables effective version control workflows
for SCADE projects while maintaining the integrity of SCADE models and configurations.
