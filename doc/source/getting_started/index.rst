Getting started
===============
To use Ansys SCADE Git extensions, you must have a valid license for Ansys SCADE.

For information on getting a licensed copy, see the
`Ansys SCADE Suite <https://www.ansys.com/products/embedded-software/ansys-scade-suite>`_
page on the Ansys website.

Requirements
------------
The ``ansys-scade-git`` package supports only the versions of Python delivered with
Ansys SCADE, starting from 2021 R2:

* 2021 R2 through 2023 R1: Python 3.7
* 2023 R2 and later: Python 3.10

Install in user mode
--------------------
The following steps are necessary for installing Ansys SCADE Git extensions in user mode. If you want to
contribute to Ansys SCADE Git extensions, see :ref:`contribute_scade_git` for installing in developer mode.

#. Before installing Ansys SCADE Git extensions in user mode, run this command to ensure that
   you have the latest version of `pip`_:

   .. code:: bash

      python -m pip install -U pip

#. Install Ansys SCADE Git extensions with this command:

   .. code:: bash

      python -m pip install ansys-scade-git

#. Complete the installation with this command:

   .. code:: bash

      python -m ansys.scade.git.register


.. toctree::
   :maxdepth: 1
   :caption: Contents:

.. LINKS AND REFERENCES
.. _pip: https://pypi.org/project/pip/
