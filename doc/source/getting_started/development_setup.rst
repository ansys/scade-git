Development Environment Setup
==============================

This guide helps you set up a development environment for contributing to Ansys SCADE Git Extensions.

Prerequisites
-------------

Before setting up the development environment:

* **Python**: Version 3.7 or 3.10 (matching your SCADE version)
  
  - SCADE 2021 R2 through 2023 R1: Python 3.7
  - SCADE 2023 R2 and later: Python 3.10

* **Git**: Version 2.0 or later
* **SCADE Suite**: A valid installation for testing
* **Text Editor/IDE**: VS Code, PyCharm, or your preferred editor

Clone the Repository
--------------------

Clone the repository from GitHub:

.. code-block:: bash

   git clone https://github.com/ansys/scade-git.git
   cd scade-git

Set Up Python Environment
--------------------------

Using Virtual Environment (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a virtual environment with the correct Python version:

.. code-block:: bash

   # For Python 3.7 (SCADE 2021 R2 - 2023 R1)
   python3.7 -m venv .venv37
   
   # For Python 3.10 (SCADE 2023 R2+)
   python3.10 -m venv .venv310

Activate the virtual environment:

**Windows:**

.. code-block:: bash

   .venv310\Scripts\activate

**Linux/Mac:**

.. code-block:: bash

   source .venv310/bin/activate

Using Conda
~~~~~~~~~~~

Alternatively, use Conda:

.. code-block:: bash

   # For Python 3.7
   conda create -n scade-git-dev python=3.7
   conda activate scade-git-dev
   
   # For Python 3.10
   conda create -n scade-git-dev python=3.10
   conda activate scade-git-dev

Install Dependencies
--------------------

Install the package in editable mode with all development dependencies:

.. code-block:: bash

   python -m pip install --upgrade pip
   python -m pip install -e ".[tests,doc,build]"

This installs:

* **Core dependencies**: ``ansys-scade-apitools``, ``dulwich``, ``lxml``
* **Test dependencies**: ``pytest``, ``pytest-cov``
* **Documentation dependencies**: ``sphinx``, ``ansys-sphinx-theme``
* **Build dependencies**: ``build``, ``twine``

Verify Installation
-------------------

Verify the installation:

.. code-block:: bash

   # Check package is installed
   python -m pip show ansys-scade-git
   
   # Verify merge tools are available
   python -m ansys.scade.git.etpmerge --version
   python -m ansys.scade.git.almgtmerge --version
   
   # Check entry points
   etpmerge --version
   almgtmerge --version

Register for Development
------------------------

Register the development version with SCADE:

.. code-block:: bash

   python -m ansys.scade.git.register

This registers your local development version, allowing you to test changes in SCADE without reinstalling.

Project Structure
-----------------

Familiarize yourself with the project layout:

.. code-block:: text

   scade-git/
   ├── src/ansys/scade/git/          # Source code
   │   ├── extension/                # GUI extension modules
   │   │   ├── gitclient.py         # Git client abstraction
   │   │   ├── gitextcore.py        # Command implementations
   │   │   ├── gitextension.py      # SCADE IDE integration
   │   │   └── ide.py               # IDE abstraction layer
   │   ├── etpmerge/                 # ETP merge tool
   │   │   ├── __main__.py          # Entry point
   │   │   ├── etpmerge3.py         # Main merge algorithm
   │   │   ├── cache.py             # Entity caching
   │   │   ├── visitor.py           # Tree traversal
   │   │   ├── fi.py                # File operations
   │   │   └── utils.py             # Utilities
   │   ├── almgtmerge/               # ALMGT merge tool
   │   │   ├── __main__.py          # Entry point
   │   │   └── almgtmerge3.py       # Merge algorithm
   │   ├── register.py               # Extension registration
   │   └── unregister.py             # Extension cleanup
   ├── tests/                        # Test suite
   │   ├── extension/                # GUI extension tests
   │   ├── etpmerge/                 # ETP merge tests
   │   ├── almgtmerge/               # ALMGT merge tests
   │   └── conftest.py              # Pytest configuration
   ├── doc/                          # Documentation
   │   ├── source/                   # User documentation (Sphinx)
   │   └── design/                   # Design documents
   ├── pyproject.toml                # Package configuration
   ├── README.rst                    # Project overview
   └── CONTRIBUTING.md               # Contribution guidelines

Development Workflow
--------------------

Making Changes
~~~~~~~~~~~~~~

1. **Create a feature branch:**

   .. code-block:: bash

      git checkout -b feature/my-feature

2. **Make your changes** in the appropriate module

3. **Test your changes** (see :ref:`development_setup:Running Tests`)

4. **Commit your changes:**

   .. code-block:: bash

      git add .
      git commit -m "feat: add new feature"

Testing Changes in SCADE
~~~~~~~~~~~~~~~~~~~~~~~~~

To test GUI extension changes:

1. **Restart SCADE Suite** after making changes
2. **Open a test project** with Git initialized
3. **Use the Git browser** to verify functionality
4. **Check the output pane** for logged messages

.. note::
   SCADE loads the extension on startup. Restart SCADE to see code changes.

Testing Merge Tools
~~~~~~~~~~~~~~~~~~~

To test merge tools without Git:

.. code-block:: bash

   # Test ETP merge
   python -m ansys.scade.git.etpmerge tests/etpmerge/resources/Nominal/base.etp \
       tests/etpmerge/resources/Nominal/local.etp \
       tests/etpmerge/resources/Nominal/remote.etp
   
   # Test ALMGT merge
   python -m ansys.scade.git.almgtmerge tests/almgtmerge/resources/Nominal/base.almgt \
       tests/almgtmerge/resources/Nominal/local.almgt \
       tests/almgtmerge/resources/Nominal/remote.almgt

To test with Git:

1. Create a test repository with SCADE files
2. Create test branches with conflicting changes
3. Attempt to merge branches
4. Verify merge tools are invoked

Running Tests
-------------

Run the entire test suite:

.. code-block:: bash

   pytest

Run specific test files:

.. code-block:: bash

   # Test Git client
   pytest tests/extension/test_gitclient.py
   
   # Test ETP merge
   pytest tests/etpmerge/test_merge.py
   
   # Test ALMGT merge
   pytest tests/almgtmerge/test_almgt_merge.py

Run with coverage:

.. code-block:: bash

   pytest --cov=ansys.scade.git --cov-report=html

View coverage report:

.. code-block:: bash

   # Open htmlcov/index.html in browser
   start htmlcov/index.html  # Windows
   open htmlcov/index.html   # Mac
   xdg-open htmlcov/index.html  # Linux

Code Quality Checks
-------------------

Run Ruff Linter
~~~~~~~~~~~~~~~

Check code style:

.. code-block:: bash

   python -m pip install ruff
   ruff check src/

Fix auto-fixable issues:

.. code-block:: bash

   ruff check --fix src/

Format Code
~~~~~~~~~~~

Format code with Ruff:

.. code-block:: bash

   ruff format src/

Type Checking (Optional)
~~~~~~~~~~~~~~~~~~~~~~~~

For type checking with mypy:

.. code-block:: bash

   python -m pip install mypy
   mypy src/ansys/scade/git/

Building Documentation
----------------------

Build the HTML documentation:

.. code-block:: bash

   cd doc
   make html

View the documentation:

.. code-block:: bash

   # Windows
   start _build/html/index.html
   
   # Linux/Mac
   open _build/html/index.html

Clean build artifacts:

.. code-block:: bash

   make clean

Debugging
---------

Debugging the GUI Extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~

To debug the SCADE extension:

1. **Add print statements or use logging:**

   .. code-block:: python

      def on_activate(self):
          self.ide.log("Debug: Entering on_activate")
          # Your code here

2. **Check SCADE output pane** for logged messages

3. **Use Python debugger:**

   Add breakpoints using ``pdb``:

   .. code-block:: python

      import pdb; pdb.set_trace()

   .. note::
      Debugger will pause SCADE. Use with caution.

Debugging Merge Tools
~~~~~~~~~~~~~~~~~~~~~

Debug merge tools by running directly:

.. code-block:: python

   # Add to merge tool code
   import pdb
   pdb.set_trace()

Or use print statements:

.. code-block:: python

   print(f"Debug: base={base_path}, local={local_path}, remote={remote_path}")

Check merge tool logs:

.. code-block:: bash

   # Git records merge tool output
   git config --get merge.etpmerge.driver

Common Issues
-------------

Import Errors
~~~~~~~~~~~~~

If you see import errors in SCADE:

* Ensure ``ansys-scade-apitools`` is installed
* Verify Python version matches SCADE version
* Check that the extension is registered

SCADE Doesn't Load Extension
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If the extension doesn't appear:

1. Check registration:

   .. code-block:: bash

      python -m ansys.scade.git.register

2. Verify SCADE finds the extension:

   * Check SCADE installation directory for ``.srg`` files
   * Look in ``SCADE_INSTALL/SCADE/configuration/Extensions/``

3. Check SCADE output pane for error messages

Test Failures
~~~~~~~~~~~~~

If tests fail:

* Ensure all test resources exist: ``tests/*/resources/``
* Check Python version matches test expectations
* Verify ``ansys-scade-apitools`` is available
* Run tests individually to isolate failures

Contributing Checklist
----------------------

Before submitting a pull request:

.. code-block:: text

   ☐ Code changes are complete and tested
   ☐ All tests pass (pytest)
   ☐ Code follows style guidelines (ruff check)
   ☐ Code is formatted (ruff format)
   ☐ Documentation is updated
   ☐ Changelog entry added (doc/changelog.d/)
   ☐ Commit messages follow convention
   ☐ Branch is up to date with main

Creating Changelog Entries
---------------------------

Add changelog entries in ``doc/changelog.d/``:

.. code-block:: bash

   # Create numbered entry (get next number from existing files)
   echo "Your change description" > doc/changelog.d/XXX.added.md

Changelog categories:

* ``.added.md``: New features
* ``.changed.md``: Changes in existing functionality
* ``.deprecated.md``: Soon-to-be removed features
* ``.removed.md``: Removed features
* ``.fixed.md``: Bug fixes
* ``.dependencies.md``: Dependency changes
* ``.maintenance.md``: Maintenance tasks
* ``.documentation.md``: Documentation changes
* ``.miscellaneous.md``: Other changes

Next Steps
----------

* Review :doc:`code_organization` to understand the codebase
* Read :doc:`testing` for detailed testing guidelines
* See :doc:`../contributing` for contribution guidelines
* Explore design documents in ``doc/design/``

.. seealso::

   :doc:`quickstart`
      Quick start tutorial for using the extension

   :doc:`testing`
      Detailed testing guide

   :doc:`code_organization`
      Code organization and architecture
