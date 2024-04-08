# Test Notes
The subdirectories `resources/*` contain unit test models with the same structure, unless specified otherwise.

They are designed for `test_merge.py`, but some of them are reused in `test_cache.py`.

## Projects
Three projects emulate the context of a merge3 operation from a configuration management tool, Git for example.

* `Local.etp` (*local*): Project file in the working area
* `Remote.etp` (*remote*): Project file to be merged into *local*
* `Base.etp` (*base*): Common ancestor project file to *local* and *remote*

A fourth optional project, `Merge.etp`, is the expected result of the merge, used as a reference.

**Note**: Most of these projects are product independent, this means neither SCADE Suite, SCADE Test or any other SCADE product. The properties are edited using a dedicated SCADE custom extension, cf. [`../tools/Properties`](../tools/Properties/readme.md).

## Glossary
* `CCP` stands for Copy/Cut/Paste. In this context, it designates objects that have been deleted and created again with the same name or key attribute, since copy/cut/paste is not available for the project entities. This limits merge impacts/conflicts when only the id changes. This is very frequent with settings. For example when someone deactivates/activates a KCG option, it is re-created with a new id.
