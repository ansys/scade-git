Quick Start Tutorial
====================

This tutorial walks you through your first Git operations with SCADE Git Extensions.

Prerequisites
-------------

Before starting, ensure you have:

* A valid Ansys SCADE license
* SCADE Suite 2021 R2 or later installed
* Git installed and configured on your system
* The ``ansys-scade-git`` package installed (see :ref:`getting_started/index:Install in user mode`)

Step 1: Register the Extension
-------------------------------

After installing the package, register the extension with SCADE:

.. code-block:: bash

   python -m ansys.scade.git.register

This command:

* Registers the Git browser extension with SCADE Suite
* Configures the merge tools for ``.etp`` and ``.almgt`` files
* Creates the necessary registry entries

**Verify Installation:**

#. Launch SCADE Suite
#. Open any SCADE project
#. Look for a **Git** browser tab in the left panel
#. Check the **Tools** menu for Git commands

Step 2: Configure Git for SCADE Projects
-----------------------------------------

Create a ``.gitattributes`` file in your SCADE project repository root to configure custom merge drivers:

.. code-block:: text

   # SCADE project files
   *.etp merge=etpmerge

   # SCADE traceability files
   *.almgt merge=almgtmerge

   # Prevent Git from treating these as binary
   *.etp -binary
   *.almgt -binary

Configure Git to use the custom merge tools:

.. code-block:: bash

   git config merge.etpmerge.name "SCADE ETP Merge Tool"
   git config merge.etpmerge.driver "etpmerge %O %A %B"

   git config merge.almgtmerge.name "SCADE ALMGT Merge Tool"
   git config merge.almgtmerge.driver "almgtmerge %O %A %B"

Step 3: Initialize a Git Repository
------------------------------------

If your SCADE project is not yet in Git:

.. code-block:: bash

   cd /path/to/your/scade/project
   git init
   git add .gitattributes
   git commit -m "Configure SCADE merge tools"

Add your project files:

.. code-block:: bash

   git add *.etp *.xscade *.ann
   git commit -m "Initial SCADE project"

Step 4: Using the Git Browser
------------------------------

Open your SCADE project in SCADE Suite.

**Refresh Git Status:**

#. Click the **Git** tab in the browser panel
#. Click the **Refresh** button (circular arrow icon) or select **Tools → Git → Refresh**
#. The browser displays files in categories:

   * **Staged**: Files ready to commit
   * **Unstaged**: Modified files not yet staged
   * **Clean**: Files with no changes
   * **External**: Files outside the Git repository

**Understanding File Icons:**

* 🟢 Green dot: Clean file (no changes)
* 🟡 Yellow dot: Modified file (unstaged)
* 🔵 Blue dot: Staged file (ready to commit)
* ⚪ Gray dot: External file (not in repository)

Step 5: Stage Changes
----------------------

After modifying files in SCADE:

**Stage Individual Files:**

#. Right-click on a file in the **Unstaged** category
#. Select **Git → Stage**

**Stage All Files:**

#. Select **Tools → Git → Stage All**
#. All unstaged files move to the **Staged** category

Step 6: Commit Changes
-----------------------

Once files are staged:

#. Select **Tools → Git → Commit** or click the commit button
#. A dialog appears with three fields:

   * **Message**: Describe your changes (required)
   * **Author**: Name and email (for example: "John Doe <john@example.com>")
   * **Committer**: Usually same as author

#. Fill in the commit message
#. Click **OK** to commit

Example commit message:

.. code-block:: text

   Add safety monitoring operator

   - Implemented threshold checking
   - Added alarm states
   - Updated project configuration

**After Commit:**

* Staged files move to the **Clean** category
* Git browser automatically refreshes
* Changes are saved to local Git history

Step 7: Unstage Files
----------------------

To remove files from staging:

**Unstage Individual Files:**

#. Right-click on a file in the **Staged** category
#. Select **Git → Unstage**

**Unstage All Files:**

#. Select **Tools → Git → Unstage All**

Step 8: Reset Changes
----------------------

To discard uncommitted changes:

.. warning::
   This operation cannot be undone. It resets files to the last commit.

#. Select **Tools → Git → Reset**
#. Confirm the operation
#. All changes since the last commit are discarded

Step 9: Working with Branches
------------------------------

Use standard Git commands from the terminal:

**Create a Branch:**

.. code-block:: bash

   git checkout -b feature/new-controller

**Switch Branches:**

.. code-block:: bash

   git checkout main

**Merge Branches:**

.. code-block:: bash

   git checkout main
   git merge feature/new-controller

The ETP and ALMGT merge tools automatically handle SCADE-specific file conflicts.

Step 10: Diff/Export for Comparison
------------------------------------

To compare branches or commits:

#. Select **Tools → Git → Diff**
#. A dialog prompts for:

   * **Branch/Commit**: What to compare (for example: ``main``, ``HEAD~1``)
   * **Export Path**: Where to export the files

#. Click **OK**
#. SCADE exports the specified version to the export path
#. Use external diff tools or SCADE's compare features

Common Workflows
----------------

Daily Development Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   1. Open SCADE project
   2. Refresh Git status (Tools → Git → Refresh)
   3. Make changes in SCADE
   4. Save project
   5. Stage changes (Tools → Git → Stage All)
   6. Commit (Tools → Git → Commit)
   7. Push to remote (terminal: git push)

Feature Branch Workflow
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create feature branch
   git checkout -b feature/my-feature

   # Make changes in SCADE
   # Use Git browser to stage and commit

   # Push feature branch
   git push -u origin feature/my-feature

   # Merge via pull request or locally:
   git checkout main
   git merge feature/my-feature

Collaborative Workflow
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Update from remote
   git pull origin main

   # If merge conflicts in .etp/.almgt files:
   # - Merge tools automatically resolve most conflicts
   # - Manual conflicts are reported in console

   # Continue working in SCADE
   # Stage and commit your changes

Troubleshooting
---------------

Extension Not Appearing
~~~~~~~~~~~~~~~~~~~~~~~

If the Git browser doesn't appear in SCADE:

#. Verify installation:

   .. code-block:: bash

      python -m pip show ansys-scade-git

#. Re-register the extension:

   .. code-block:: bash

      python -m ansys.scade.git.unregister
      python -m ansys.scade.git.register

#. Restart SCADE Suite

Files Not Showing Status
~~~~~~~~~~~~~~~~~~~~~~~~~

If files don't show correct status:

* Click **Refresh** in the Git browser
* Ensure the project file is inside a Git repository
* Check that Git is properly initialized (``ls -la .git``)

Merge Tool Not Working
~~~~~~~~~~~~~~~~~~~~~~

If merge tools aren't invoked:

#. Verify ``.gitattributes`` configuration
#. Check Git configuration:

   .. code-block:: bash

      git config --get merge.etpmerge.driver
      git config --get merge.almgtmerge.driver

#. Ensure ``etpmerge`` and ``almgtmerge`` are in PATH:

   .. code-block:: bash

      etpmerge --version
      almgtmerge --version

Next Steps
----------

* Learn about :doc:`../architecture` to understand the system design
* Review :doc:`../gui-extensions/index` for detailed feature documentation
* Explore :doc:`../merge-tools/index` for merge tool configuration
* See :doc:`development_setup` if you want to contribute

.. seealso::

   :doc:`index`
      Installation instructions

   :doc:`../gui-extensions/index`
      Complete GUI extension documentation

   :doc:`../merge-tools/index`
      Merge tool reference
