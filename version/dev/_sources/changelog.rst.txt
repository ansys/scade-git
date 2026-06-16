.. _ref_release_notes:

Release notes
#############

This document contains the release notes for the project.

.. vale off

.. towncrier release notes start

`0.2.0 <https://github.com/ansys/scade-git/releases/tag/v0.2.0>`_ - March 21, 2025
==================================================================================

.. tab-set::


  .. tab-item:: Added

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - feat: Add register and unregister entry points for Extensions Manager
          - `#49 <https://github.com/ansys/scade-git/pull/49>`_


  .. tab-item:: Fixed

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - fix: Limit flit version
          - `#48 <https://github.com/ansys/scade-git/pull/48>`_


  .. tab-item:: Dependencies

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - build(deps): bump the dependencies group with 4 updates
          - `#40 <https://github.com/ansys/scade-git/pull/40>`_

        * - build(deps): bump the dependencies group with 5 updates
          - `#41 <https://github.com/ansys/scade-git/pull/41>`_

        * - build(deps): bump the dependencies group with 2 updates
          - `#43 <https://github.com/ansys/scade-git/pull/43>`_

        * - build(deps): bump the dependencies group with 3 updates
          - `#45 <https://github.com/ansys/scade-git/pull/45>`_

        * - build(deps): bump ansys-sphinx-theme from 1.2.6 to 1.3.2 in the dependencies group
          - `#46 <https://github.com/ansys/scade-git/pull/46>`_


  .. tab-item:: Documentation

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - chore: update CHANGELOG for v0.1.3
          - `#38 <https://github.com/ansys/scade-git/pull/38>`_


  .. tab-item:: Maintenance

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - ci: Upload the coverage results
          - `#28 <https://github.com/ansys/scade-git/pull/28>`_

        * - build(deps): bump codecov/codecov-action from 4 to 5 in the actions group
          - `#42 <https://github.com/ansys/scade-git/pull/42>`_

        * - ci: Fix steps for creating a release
          - `#47 <https://github.com/ansys/scade-git/pull/47>`_


  .. tab-item:: Test

    .. list-table::
        :header-rows: 0
        :widths: auto

        * - build(deps): bump the dependencies group with 3 updates
          - `#44 <https://github.com/ansys/scade-git/pull/44>`_


`0.1.3 <https://github.com/ansys/scade-git/releases/tag/v0.1.3>`_ - 2024-09-26
==============================================================================

Fixed
^^^^^

- fix: Make sure the directory %APPDATA%\SCADE\Customize exists when registering the package `#31 <https://github.com/ansys/scade-git/pull/31>`_
- fix:add changelog action in cicd `#34 <https://github.com/ansys/scade-git/pull/34>`_
- fix: The package is not loaded by SCADE 2024 R2 `#36 <https://github.com/ansys/scade-git/pull/36>`_
- fix: Update the change log only when creating a new release `#37 <https://github.com/ansys/scade-git/pull/37>`_


Documentation
^^^^^^^^^^^^^

- maint: technical review `#25 <https://github.com/ansys/scade-git/pull/25>`_
- docs: Add the parameter --user in the pip install command line `#33 <https://github.com/ansys/scade-git/pull/33>`_


Maintenance
^^^^^^^^^^^

- ci: use trusted publishers `#26 <https://github.com/ansys/scade-git/pull/26>`_
- ci: remove the artifact examples `#27 <https://github.com/ansys/scade-git/pull/27>`_

.. vale on