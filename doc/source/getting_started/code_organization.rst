Code Organization
=================

This guide provides an overview of the codebase structure to help you navigate and understand the project.

Repository Structure
--------------------

.. code-block:: text

   scade-git/
   ├── src/ansys/scade/git/          # Source code (main package)
   ├── tests/                        # Test suite
   ├── doc/                          # Documentation
   ├── pyproject.toml                # Package configuration
   ├── README.rst                    # Project overview
   ├── CONTRIBUTING.md               # Contribution guidelines
   ├── LICENSE                       # MIT license
   └── tox.ini                       # Test automation config

Source Code Structure
---------------------

The source code is organized under ``src/ansys/scade/git/``:

.. code-block:: text

   src/ansys/scade/git/
   ├── extension/                    # GUI extension (SCADE IDE integration)
   │   ├── gitclient.py             # Git operations wrapper
   │   ├── gitextcore.py            # Command implementations
   │   ├── gitextension.py          # SCADE-specific IDE integration
   │   └── ide.py                   # IDE abstraction layer
   ├── etpmerge/                     # ETP merge tool
   │   ├── __main__.py              # command-line tool entry point
   │   ├── etpmerge3.py             # Three-way merge algorithm
   │   ├── cache.py                 # Entity caching for merge
   │   ├── visitor.py               # Project tree traversal
   │   ├── fi.py                    # File manipulation utilities
   │   └── utils.py                 # General utilities
   ├── almgtmerge/                   # ALMGT merge tool
   │   ├── __main__.py              # command-line tool entry point
   │   └── almgtmerge3.py           # Three-way merge algorithm
   ├── register.py                   # Extension registration script
   ├── unregister.py                 # Extension cleanup script
   ├── __init__.py                  # Package initialization
   ├── git.srg                      # Extension registry (all Python versions)
   ├── git-37.srg                   # Extension registry (Python 3.7)
   └── git-310.srg                  # Extension registry (Python 3.10)

Component Overview
------------------

1. GUI Extension (extension/)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Integrates Git version control into SCADE Suite IDE.

**Key Files:**

* **gitclient.py**: Git operations abstraction

  - Abstract base class ``GitClient``
  - Repository discovery
  - File status management
  - Git operations (stage, unstage, commit, reset)
  - Wraps Dulwich library

* **ide.py**: IDE abstraction layer

  - Abstract base class ``Ide``
  - Abstract base class ``Command``
  - Enables testing without SCADE
  - Enables potential support for other IDEs

* **gitextension.py**: SCADE-specific implementation

  - ``Studio`` class (implements ``Ide``)
  - Creates Git browser, menus, toolbars
  - Handles SCADE-specific UI interactions
  - Implements ``GitClient`` for IDE logging

* **gitextcore.py**: Git command implementations

  - ``CmdRefresh``: Update Git status
  - ``CmdStage`` / ``CmdStageAll``: Stage files
  - ``CmdUnstage`` / ``CmdUnstageAll``: Unstage files
  - ``CmdCommit``: Commit staged changes
  - ``CmdReset``: Reset to last commit
  - ``CmdDiff``: Export branch for comparison

**Class Hierarchy:**

.. code-block:: text

   Ide (Abstract)
   └── Studio (SCADE implementation)

   GitClient (Abstract)
   └── StudioGitClient (SCADE implementation)

   Command (Abstract)
   ├── CmdRefresh
   └── GitRepoCommand (Abstract)
       ├── CmdStage
       ├── CmdStageAll
       ├── CmdUnstage
       ├── CmdUnstageAll
       ├── CmdCommit
       ├── CmdReset
       └── CmdDiff

**Dependencies:**

* ``dulwich``: Pure Python Git implementation
* ``ansys-scade-apitools``: SCADE API access

2. ETP Merge Tool (etpmerge/)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Intelligent three-way merge of SCADE project files (.etp).

**Key Files:**

* **etpmerge3.py**: Main merge algorithm

  - ``merge3()`` function: Entry point
  - Three-way merge logic
  - Conflict detection
  - Result generation

* **cache.py**: Entity caching

  - ``CacheMaps`` class: ID-to-entity mappings
  - Tracks entities across base/local/remote
  - Resolves entity references by ID

* **visitor.py**: Tree traversal

  - ``Visitor`` class: Walks project tree
  - ``ProjectListener``: Callback interface
  - Enables systematic project processing

* **fi.py**: File operations

  - ``FileInfo`` class: File manipulation
  - Copy, overwrite, backup operations
  - Path management

* **utils.py**: Utilities

  - XML processing helpers
  - Pretty printing
  - Error handling

**Merge Algorithm Flow:**

.. code-block:: text

   1. Parse base, local, remote projects
   2. Build CacheMaps for entity tracking
   3. Compare trees:
      - Detect additions, deletions, moves
      - Compare properties
   4. Merge changes:
      - Apply non-conflicting changes
      - Report conflicts
   5. Write merged result to local file

**Dependencies:**

* ``ansys-scade-apitools``: SCADE project API
* ``lxml``: XML processing

3. ALMGT Merge Tool (almgtmerge/)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose:** Conflict-free merge of SCADE traceability files (.almgt).

**Key Files:**

* **almgtmerge3.py**: Complete implementation

  - ``merge3()`` function: Entry point
  - Set-based merge algorithm
  - XML parsing and generation
  - Always succeeds (no conflicts)

**Merge Algorithm:**

.. code-block:: text

   Merged = (Local - Base) ∪ (Remote - Base)

   1. Parse XML files
   2. Build dictionaries:
      - Object ID → Requirements
   3. Compute set differences:
      - Local changes = Local - Base
      - Remote changes = Remote - Base
   4. Union of changes
   5. Generate merged XML

**Dependencies:**

* ``lxml``: XML processing

Configuration Files
-------------------

1. pyproject.toml
~~~~~~~~~~~~~~~~~

Package configuration using modern Python packaging:

.. code-block:: toml

   [project]
   name = "ansys-scade-git"
   version = "0.3.dev0"
   dependencies = [
       "ansys-scade-apitools",
       "dulwich==0.24.1",
       "lxml",
   ]

   [project.scripts]
   etpmerge = "ansys.scade.git.etpmerge.__main__:main"
   almgtmerge = "ansys.scade.git.almgtmerge.__main__:main"

**Key sections:**

* ``[project]``: Package metadata
* ``[project.dependencies]``: Runtime dependencies
* ``[project.optional-dependencies]``: Development dependencies
* ``[project.scripts]``: Command-line entry points
* ``[project.entry-points."ansys.scade.registry"]``: SCADE extension registration
* ``[tool.ruff]``: Linter configuration

2. Extension Registry Files (.srg)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

SCADE extension registration:

* **git.srg**: All Python versions (fallback)
* **git-37.srg**: Python 3.7 specific (SCADE 2021 R2 - 2023 R1)
* **git-310.srg**: Python 3.10 specific (SCADE 2023 R2+)

Format:

.. code-block:: xml

   <?xml version="1.0"?>
   <ExtensionRegistry>
       <Extension id="ansys.scade.git" name="Git">
           <Contribution id="git_browser" type="Browser">
               <Module>ansys.scade.git.extension.gitextension</Module>
               <Function>load</Function>
           </Contribution>
       </Extension>
   </ExtensionRegistry>

Documentation Structure
-----------------------

.. code-block:: text

   doc/
   ├── source/                       # User documentation (Sphinx)
   │   ├── index.rst                # Documentation home
   │   ├── architecture.rst         # Architecture overview
   │   ├── getting_started/         # Installation and tutorials
   │   │   ├── index.rst           # Installation
   │   │   ├── quickstart.rst      # Quick start tutorial
   │   │   ├── development_setup.rst # Dev environment setup
   │   │   ├── testing.rst         # Testing guide
   │   │   └── code_organization.rst # This file
   │   ├── gui-extensions/          # GUI extension docs
   │   │   └── index.rst
   │   ├── merge-tools/             # Merge tool docs
   │   │   ├── index.rst
   │   │   ├── etp.rst             # ETP merge documentation
   │   │   └── almgt.rst           # ALMGT merge documentation
   │   └── _static/                 # Static assets
   ├── design/                       # Design documents (developer)
   │   ├── README.md                # Design doc index
   │   ├── 01_git_client.md        # Git client design
   │   ├── 02_gui_extension.md     # GUI extension design
   │   ├── 03_etp_merge.md         # ETP merge design
   │   └── 04_almgt_merge.md       # ALMGT merge design
   ├── changelog.d/                  # Changelog fragments
   ├── make.bat                      # Windows doc build
   └── Makefile                      # Linux/Mac doc build

Test Structure
--------------

.. code-block:: text

   tests/
   ├── conftest.py                   # Pytest fixtures
   ├── test_utils.py                 # Utility tests
   ├── extension/                    # Extension tests
   │   ├── test_gitclient.py        # Git client tests
   │   ├── test_gitextcore.py       # Command tests
   │   ├── resources/               # Test data
   │   └── ref/                     # Reference files
   ├── etpmerge/                     # ETP merge tests
   │   ├── test_merge.py            # Merge tests
   │   ├── test_cache.py            # Cache tests
   │   └── resources/               # Test projects
   │       ├── Nominal/             # Basic merge
   │       ├── Advanced/            # Complex project
   │       ├── DelBoth/             # Conflict scenarios
   │       └── ...
   └── almgtmerge/                   # ALMGT merge tests
       ├── test_almgt_merge.py      # Merge tests
       └── resources/               # Test files
           ├── Nominal/
           ├── DelBoth/
           └── ...

Entry Points and Execution
---------------------------

GUI Extension
~~~~~~~~~~~~~

**Entry Point:**

1. SCADE loads extension on startup
2. Calls ``load()`` in ``gitextension.py``
3. Creates ``Studio`` instance
4. Registers commands and browser

**Execution Flow:**

.. code-block:: text

   SCADE Startup
   → Load Extension (load function)
   → Create Studio instance
   → Register Git browser
   → Add menus and commands

   User Action (e.g., "Stage All")
   → Command.on_activate()
   → CmdStageAll.on_activate()
   → GitClient.stage()
   → Dulwich operations
   → Refresh Git browser

Merge Tools
~~~~~~~~~~~

**Entry Points:**

* **CLI**: ``etpmerge`` / ``almgtmerge`` commands
* **Git**: Called by Git during merge operations

**Execution Flow:**

.. code-block:: text

   Git Merge
   → Detects conflict in .etp file
   → Reads .gitattributes
   → Finds merge driver "etpmerge"
   → Executes: etpmerge %O %A %B
   → merge3(base, local, remote)
   → Merge algorithm
   → Write result to local
   → Return exit code (0=success, 1=conflict)

Registration Scripts
~~~~~~~~~~~~~~~~~~~~

**register.py:**

.. code-block:: text

   python -m ansys.scade.git.register
   → Copy .srg files to SCADE
   → Configure Git merge drivers
   → Report success

**unregister.py:**

.. code-block:: text

   python -m ansys.scade.git.unregister
   → Remove .srg files from SCADE
   → Clean up registry
   → Report success

Naming Conventions
------------------

File Naming
~~~~~~~~~~~

* **Modules**: lowercase with underscores (``gitclient.py``)
* **Classes**: PascalCase (``GitClient``, ``CmdRefresh``)
* **Functions**: lowercase with underscores (``find_git_repo``)
* **Constants**: UPPERCASE (``GIT_STATUS_CLEAN``)

Code Organization
~~~~~~~~~~~~~~~~~

* **One class per file** (generally)
* **Related functions grouped** in modules
* **Public API first**, private functions last
* **Imports organized**: standard library → third-party → local

Docstring Style
~~~~~~~~~~~~~~~

* **Module docstrings**: Brief description
* **Class docstrings**: Purpose and usage
* **Method docstrings**: Google style with Args/Returns/Raises

Example:

.. code-block:: python

   def stage(self, files: List[str]) -> None:
       """Stage files for commit.

       Args:
           files: List of file paths to stage.

       Raises:
           GitError: If files cannot be staged.
       """

Finding Code
------------

By Feature
~~~~~~~~~~

**Want to understand...**

* **Git operations**: Start with ``extension/gitclient.py``
* **IDE commands**: Read ``extension/gitextcore.py``
* **Browser UI**: Check ``extension/gitextension.py``
* **ETP merge**: Study ``etpmerge/etpmerge3.py``
* **ALMGT merge**: See ``almgtmerge/almgtmerge3.py``

By Use Case
~~~~~~~~~~~

**"How do I..."**

* **Add a new Git command**: Extend ``Command`` in ``gitextcore.py``
* **Modify merge algorithm**: Edit ``etpmerge3.py`` or ``almgtmerge3.py``
* **Change browser display**: Update ``gitextension.py``
* **Add new file type support**: Extend merge tool or create new one

Common Patterns
---------------

Command Pattern
~~~~~~~~~~~~~~~

All Git commands follow this pattern:

.. code-block:: python

   class CmdMyCommand(GitRepoCommand):
       def __init__(self, ide: Ide, *args, **kwargs):
           super().__init__(ide, *args, **kwargs)

       def on_enable(self) -> bool:
           """Return True if command should be enabled."""
           return super().on_enable()  # Checks for valid repo

       def on_activate(self):
           """Execute the command."""
           # Implementation here

Abstract Base Classes
~~~~~~~~~~~~~~~~~~~~~

Abstraction for extensibility:

.. code-block:: python

   class Ide(metaclass=ABCMeta):
       @abstractmethod
       def log(self, text: str):
           """Log a message."""
           pass

Caching Pattern
~~~~~~~~~~~~~~~

Cache expensive operations:

.. code-block:: python

   class GitClient:
       def refresh(self, project_path: str):
           """Refresh status and rebuild cache."""
           self.files_status = {}  # Clear cache
           # Rebuild cache
           for file in self.get_all_files():
               self.files_status[file] = self.compute_status(file)

Next Steps
----------

* Review :doc:`development_setup` for environment setup
* Read :doc:`testing` for testing guidelines
* Study design documents in ``doc/design/``
* Explore the codebase following this guide

.. seealso::

   :doc:`development_setup`
      Development environment setup

   :doc:`testing`
      Testing guide

   :doc:`quickstart`
      Quick start tutorial

   :doc:`../architecture`
      Architecture overview
