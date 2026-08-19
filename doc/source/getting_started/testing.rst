Testing Guide
=============

This guide covers testing practices for Ansys SCADE Git Extensions.

Overview
--------

The test suite ensures code quality and prevents regressions. Tests are organized by component:

* **Extension tests**: GUI extension and Git client functionality
* **ETP merge tests**: Project file merge logic
* **ALMGT merge tests**: Traceability file merge logic

Test Framework
--------------

The project uses **pytest** as the test framework.

Key features:

* **Fixtures**: Reusable test setup in ``conftest.py``
* **Parametrization**: Run same test with different inputs
* **Coverage**: Track code coverage with ``pytest-cov``
* **Mocking**: Mock SCADE API and Git operations

Running Tests
-------------

Run All Tests
~~~~~~~~~~~~~

.. code-block:: bash

   pytest

Run with verbose output:

.. code-block:: bash

   pytest -v

Run Specific Tests
~~~~~~~~~~~~~~~~~~

Run a specific test file:

.. code-block:: bash

   pytest tests/extension/test_gitclient.py

Run a specific test function:

.. code-block:: bash

   pytest tests/extension/test_gitclient.py::test_find_git_repo

Run tests matching a pattern:

.. code-block:: bash

   pytest -k "merge"

Run by Test Category
~~~~~~~~~~~~~~~~~~~~

Run tests by directory:

.. code-block:: bash

   # Extension tests
   pytest tests/extension/
   
   # ETP merge tests
   pytest tests/etpmerge/
   
   # ALMGT merge tests
   pytest tests/almgtmerge/

Code Coverage
-------------

Generate Coverage Report
~~~~~~~~~~~~~~~~~~~~~~~~

Run tests with coverage:

.. code-block:: bash

   pytest --cov=ansys.scade.git

Generate HTML coverage report:

.. code-block:: bash

   pytest --cov=ansys.scade.git --cov-report=html

View the report:

.. code-block:: bash

   # Windows
   start htmlcov/index.html
   
   # Linux/Mac
   open htmlcov/index.html

Coverage Goals
~~~~~~~~~~~~~~

* **Overall**: Aim for >80% code coverage
* **Critical paths**: Merge algorithms should have >90% coverage
* **Edge cases**: Test error conditions and boundary cases

Test Organization
-----------------

Test Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   tests/
   ├── conftest.py                   # Shared fixtures
   ├── test_utils.py                 # Utility tests
   ├── extension/                    # Extension tests
   │   ├── test_gitclient.py        # Git client tests
   │   ├── test_gitextcore.py       # Command tests
   │   ├── resources/                # Test data
   │   └── ref/                      # Reference files
   ├── etpmerge/                     # ETP merge tests
   │   ├── test_merge.py            # Merge algorithm tests
   │   ├── test_cache.py            # Cache tests
   │   └── resources/                # Test projects
   │       ├── Nominal/              # Normal merge scenario
   │       ├── DelBoth/              # Delete conflict
   │       ├── Advanced/             # Complex project
   │       └── ...
   └── almgtmerge/                   # ALMGT merge tests
       ├── test_almgt_merge.py      # Merge tests
       └── resources/                # Test traceability files
           ├── Nominal/
           ├── DelBoth/
           └── ...

Test Fixtures
~~~~~~~~~~~~~

Common fixtures are defined in ``conftest.py``:

.. code-block:: python

   @pytest.fixture
   def temp_git_repo(tmp_path):
       """Create a temporary Git repository."""
       repo_path = tmp_path / "test_repo"
       repo_path.mkdir()
       # Initialize Git repo
       return repo_path

Use fixtures in tests:

.. code-block:: python

   def test_something(temp_git_repo):
       # temp_git_repo is automatically provided
       assert temp_git_repo.exists()

Writing Tests
-------------

Test Naming Conventions
~~~~~~~~~~~~~~~~~~~~~~~

* Test files: ``test_*.py``
* Test functions: ``test_*()``
* Test classes: ``Test*``

Example:

.. code-block:: python

   # tests/extension/test_gitclient.py
   
   def test_find_git_repo():
       """Test repository discovery."""
       pass
   
   def test_get_file_status():
       """Test file status retrieval."""
       pass
   
   class TestGitClient:
       def test_init(self):
           """Test GitClient initialization."""
           pass

Test Structure
~~~~~~~~~~~~~~

Follow the **Arrange-Act-Assert** pattern:

.. code-block:: python

   def test_stage_file():
       # Arrange: Set up test data
       client = MockGitClient()
       file_path = "test.etp"
       
       # Act: Execute the operation
       client.stage([file_path])
       
       # Assert: Verify the result
       status = client.get_file_status(file_path)
       assert status == GitStatus.added

Using Parametrize
~~~~~~~~~~~~~~~~~

Test multiple scenarios with ``pytest.mark.parametrize``:

.. code-block:: python

   @pytest.mark.parametrize("file_path,expected_status", [
       ("modified.etp", GitStatus.modified_unstaged),
       ("new.etp", GitStatus.untracked),
       ("clean.etp", GitStatus.clean),
   ])
   def test_file_status(file_path, expected_status):
       client = MockGitClient()
       status = client.get_file_status(file_path)
       assert status == expected_status

Testing Git Client
------------------

Test Structure
~~~~~~~~~~~~~~

Git client tests use real Git repositories in temporary directories:

.. code-block:: python

   import pytest
   from pathlib import Path
   from ansys.scade.git.extension.gitclient import find_git_repo, GitStatus
   
   def test_find_git_repo(tmp_path):
       """Test Git repository discovery."""
       # Create repo structure
       repo_path = tmp_path / "repo"
       repo_path.mkdir()
       git_dir = repo_path / ".git"
       git_dir.mkdir()
       
       # Test discovery
       project_path = repo_path / "subdir" / "project.etp"
       project_path.parent.mkdir()
       
       found = find_git_repo(str(project_path))
       assert found == str(repo_path)

Mocking SCADE API
~~~~~~~~~~~~~~~~~

Since SCADE API requires SCADE Suite, mock it in tests:

.. code-block:: python

   from unittest.mock import Mock, MagicMock
   
   def test_ide_integration():
       # Mock SCADE IDE
       mock_ide = Mock()
       mock_ide.get_active_project.return_value = Mock(pathname="/path/to/project.etp")
       
       # Test with mock
       command = CmdRefresh(mock_ide, "Refresh", "", "", "")
       command.on_activate()
       
       # Verify interactions
       mock_ide.log.assert_called()

Testing ETP Merge
-----------------

Test Data Structure
~~~~~~~~~~~~~~~~~~~

ETP merge tests use prepared test projects in ``tests/etpmerge/resources/``:

.. code-block:: text

   tests/etpmerge/resources/Nominal/
   ├── base.etp      # Common ancestor
   ├── local.etp     # Local changes
   ├── remote.etp    # Remote changes
   └── expected.etp  # Expected merge result

Each scenario tests specific merge cases:

* **Nominal**: Normal merge with non-conflicting changes
* **DelBoth**: Both sides delete same file
* **Advanced**: Complex project structure
* **Configurations**: Configuration-specific properties
* **Properties**: Property conflicts

Writing Merge Tests
~~~~~~~~~~~~~~~~~~~

Basic merge test structure:

.. code-block:: python

   import pytest
   from pathlib import Path
   from ansys.scade.git.etpmerge.etpmerge3 import merge3
   
   def test_nominal_merge():
       """Test merge of non-conflicting changes."""
       # Arrange: Get test files
       base = "tests/etpmerge/resources/Nominal/base.etp"
       local = "tests/etpmerge/resources/Nominal/local.etp"
       remote = "tests/etpmerge/resources/Nominal/remote.etp"
       expected = "tests/etpmerge/resources/Nominal/expected.etp"
       
       # Act: Perform merge
       result = merge3(base, local, remote)
       
       # Assert: Check result
       assert result == 0  # Success
       assert files_equal(local, expected)

Conflict Testing
~~~~~~~~~~~~~~~~

Test merge conflict detection:

.. code-block:: python

   def test_delete_conflict():
       """Test conflict when both sides delete same file."""
       base = "tests/etpmerge/resources/DelBoth/base.etp"
       local = "tests/etpmerge/resources/DelBoth/local.etp"
       remote = "tests/etpmerge/resources/DelBoth/remote.etp"
       
       # Merge should report conflict
       result = merge3(base, local, remote)
       assert result == 1  # Conflict detected

Testing ALMGT Merge
-------------------

Test Data Structure
~~~~~~~~~~~~~~~~~~~

ALMGT tests follow similar structure:

.. code-block:: text

   tests/almgtmerge/resources/Nominal/
   ├── base.almgt      # Base traceability
   ├── local.almgt     # Local changes
   ├── remote.almgt    # Remote changes
   └── expected.almgt  # Expected result

Writing ALMGT Tests
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from ansys.scade.git.almgtmerge.almgtmerge3 import merge3
   
   def test_almgt_merge():
       """Test ALMGT traceability merge."""
       base = "tests/almgtmerge/resources/Nominal/base.almgt"
       local = "tests/almgtmerge/resources/Nominal/local.almgt"
       remote = "tests/almgtmerge/resources/Nominal/remote.almgt"
       
       result = merge3(base, local, remote)
       assert result == 0  # Always succeeds (conflict-free)

Creating Test Data
------------------

Creating ETP Test Projects
~~~~~~~~~~~~~~~~~~~~~~~~~~

To create new test scenarios:

1. **Create base project in SCADE**
2. **Export to base.etp**
3. **Create two branches**
4. **Make different changes in each branch**
5. **Export to local.etp and remote.etp**
6. **Manually merge or create expected.etp**

Creating ALMGT Test Files
~~~~~~~~~~~~~~~~~~~~~~~~~

To create ALMGT test data:

1. **Create base traceability file**
2. **Create local version with added/removed links**
3. **Create remote version with different changes**
4. **Determine expected merge result using set logic**

Testing Best Practices
----------------------

Write Clear Tests
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Good: Clear test name and structure
   def test_stage_file_moves_to_staged_category():
       """Test that staging a file updates its status to staged."""
       client = create_test_client()
       client.stage(["file.etp"])
       assert client.get_file_status("file.etp") == GitStatus.added
   
   # Bad: Unclear test
   def test_stage():
       c = get_client()
       c.stage(["f"])
       assert c.get_file_status("f") == 1

Test One Thing
~~~~~~~~~~~~~~

Each test should verify one behavior:

.. code-block:: python

   # Good: Tests one behavior
   def test_stage_file():
       client.stage(["file.etp"])
       assert client.get_file_status("file.etp") == GitStatus.added
   
   def test_unstage_file():
       client.unstage(["file.etp"])
       assert client.get_file_status("file.etp") == GitStatus.modified_unstaged
   
   # Bad: Tests multiple things
   def test_stage_and_unstage():
       client.stage(["file.etp"])
       assert client.get_file_status("file.etp") == GitStatus.added
       client.unstage(["file.etp"])
       assert client.get_file_status("file.etp") == GitStatus.modified_unstaged

Use Descriptive Assertions
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Good: Clear assertion message
   assert result == expected, f"Expected {expected}, got {result}"
   
   # Good: Use specific assertions
   assert len(files) == 3
   assert "test.etp" in files
   assert files[0].startswith("/path")
   
   # Bad: Generic assertion
   assert x

Clean Up Resources
~~~~~~~~~~~~~~~~~~

Use fixtures for cleanup:

.. code-block:: python

   @pytest.fixture
   def temp_repo(tmp_path):
       """Create and cleanup temporary repo."""
       repo_path = tmp_path / "repo"
       repo_path.mkdir()
       # Setup
       yield repo_path
       # Cleanup happens automatically

Continuous Integration
----------------------

Tests run automatically on:

* **Pull requests**: All tests must pass
* **Main branch**: After merge
* **Release branches**: Before release

CI Configuration
~~~~~~~~~~~~~~~~

See ``.github/workflows/ci_cd.yml`` for CI setup.

Local CI Simulation
~~~~~~~~~~~~~~~~~~~

Run tests as CI does:

.. code-block:: bash

   # Run all tests with coverage
   pytest --cov=ansys.scade.git --cov-report=term-missing
   
   # Check code style
   ruff check src/
   
   # Format code
   ruff format src/

Debugging Test Failures
------------------------

Verbose Output
~~~~~~~~~~~~~~

.. code-block:: bash

   # Show print statements
   pytest -s
   
   # Show full diff on assertion failures
   pytest -vv

Run One Test
~~~~~~~~~~~~

.. code-block:: bash

   pytest tests/extension/test_gitclient.py::test_find_git_repo -v

Use Debugger
~~~~~~~~~~~~

.. code-block:: python

   def test_something():
       import pdb; pdb.set_trace()  # Breakpoint
       # Test code

Or run with pytest's debugger:

.. code-block:: bash

   pytest --pdb

Check Test Data
~~~~~~~~~~~~~~~

Verify test data exists and is correct:

.. code-block:: bash

   ls tests/etpmerge/resources/Nominal/
   cat tests/etpmerge/resources/Nominal/base.etp

Next Steps
----------

* Review :doc:`development_setup` for environment setup
* Study existing tests in ``tests/`` directory
* Read design documents for component details
* See :doc:`../contributing` for contribution workflow

.. seealso::

   :doc:`development_setup`
      Development environment setup

   :doc:`quickstart`
      Quick start tutorial

   :doc:`code_organization`
      Code organization guide
