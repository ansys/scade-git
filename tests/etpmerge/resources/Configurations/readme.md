# Configurations: Test Notes
## Goals
This test suite is used to ensure the configurations and their properties are properly merged/reconciled.

It does not consider the use cases which have their own test suites, for example:
* New/deleted/modified properties
* Values: Conflicts, merge of lists, etc.
* State of the properties' owners: The properties are all linked to the projects
* The impact on the properties defining the association Tool (0..1) - (*) Configuration

**Note**: The test projects use the extension `Tools/Properties/EtpMerge` to edit a few properties depending on a configuration.

## Configurations
* `Nominal`: Configuration kept in the three projects
* `CCP Local`: Configuration deleted/created again with same name in *local*
* `CCP Remote`: Configuration deleted/created again with same name in *remote*
* `New All`: Configuration created with same name in both *local* and *remote*, not existing in *base*
* `New Remote`: Configuration created in *remote*
* `New Local`: Configuration created in *local*
* `Del Remote`: Configuration deleted in *remote*
* `Del Local`: Configuration deleted in *local*
* `Rename All`: Configuration renamed in both *local* and *remote*, with conflict
* `Rename Remote`: Configuration renamed in *remote*
* `Rename Local`: Configuration renamed in *local*

## Properties
There is only one property for this test suite, SCALAR_1, attached to the project. Its value is the name of the linked configuration to ease the debugging and the verification of the result.
