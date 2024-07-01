Merge tools
-----------

The Ansys SCADE Git Extension merge tools address Ansys SCADE files where
default textual merge is not appropriate.
They merge files derived from a common ancestor, using the `merge 3`_
technique, and are intended to be used as part of the merge feature of a
version control system such as `Git`_.

The post-installation step of this package registers the tools to `Git`_.

If you are using a different version control system, please refer to its
documentation for declaring the merge tools. They all have the following
interface:

.. code::

  usage: <tool> [-h] -l <local> -r <remote> -b <base> -m <merged>

  options:
  -h, --help            show this help message and exit
  -l <local>, --local <local>
                          local file
  -r <remote>, --remote <remote>
                          remote file
  -b <base>, --base <base>
                          base file
  -m <merged>, --merged <merged>
                          merged file

.. toctree::
   :maxdepth: 1

   etp
   almgt

.. _Git: https://git-scm.com
.. _merge 3: https://en.wikipedia.org/wiki/Merge_(version_control)#Three-way_merge
