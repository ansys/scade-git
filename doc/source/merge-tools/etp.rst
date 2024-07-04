Project file
============

Overview
--------

The project files (ETP) are XML files with locally unique identifiers which
must be considered for merging.

The ``etpmerge`` utility merges two Ansys SCADE project files derived from a common ancestor.

Non-conflicting changes are merged automatically in the output file.
Any conflicts are reported at the end of the file for manual analysis and resolution.
This is most useful when models are versioned in a configuration management tool such as `Git`_.

To minimize conflicts, the algorithm is aware of identifiers and semantic properties,
such as the uniqueness of configuration names or file paths.

Conflict resolution
-------------------
Conflicts are *always* resolved using current branch changes. Each conflict is
also reported at the end of the file, after the XML tree, and includes the
following information:

* Context: ``tag``, ``id`` or ``name`` of the object. For clarity, this context
  includes the context of the owner for properties
* Local attribute values
* Remote attribute values

Each report must be manually analyzed. If remote changes are to be kept, the
report includes enough information to manually apply these changes in the file.
Then, deleting the conflict report block marks the conflict as resolved.

Conflict reporting pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code::

  <?xml version="1.0" encoding="UTF-8"?>
  <Project id="1" oid_count="123" defaultConfiguration="2">
     ...
     ...
     ...
  </Project>
  <<<<<<< HEAD
  <context>
  -> local <attribute> = "<value>"
  =======
  -> remote <attribute> = "<value>"
  >>>>>>>

Below are some samples for different conflict types.

Attribute conflict
^^^^^^^^^^^^^^^^^^
XML attributes have conflicting values for a node in the model.

*E.g.:* Attributes ``name`` and ``extensions`` are in conflict:

.. code::

  <<<<<<< HEAD
  Folder "14" ("C Files")
  -> local name = "C Files"
  -> local extensions = "c"
  =======
  -> remote name = "C++ Files"
  -> remote extensions = "cpp;c++"
  >>>>>>>

Hierarchy conflict
^^^^^^^^^^^^^^^^^^
An element was moved to different places in both projects.

*E.g.:* The folder ``Runtime Files`` was moved to folder ``C Files`` locally,
and moved as a root folder of the project remotely:

.. code::

  <<<<<<< HEAD
  Folder "109" ("Runtime Files")
  -> local owner = "C Files" ("14")
  =======
  -> remote owner = "<project>" ("1")
  >>>>>>>

Property conflict
^^^^^^^^^^^^^^^^^
A property has conflicting values.

*E.g.:* The value of property ``@GENERATOR:ROOTNODE`` is in conflict:

.. code::

  <<<<<<< HEAD
  Prop "31" ("@GENERATOR:ROOTNODE")
      from: Project "1" ("<project>")
  -> local value = "FallingEdge"
  =======
  -> remote value = "RisingEdge"
  >>>>>>>

*Note:* The context contains the owner of the property, which is the project in this example.

.. LINKS AND REFERENCES
.. _Git: https://git-scm.com
