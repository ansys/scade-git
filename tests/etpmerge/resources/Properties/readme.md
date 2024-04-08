# Properties: Test Notes
## Goals
This test suite is used to ensure the properties and their values are properly merged/reconciled.

It does not consider the use cases which have their own test suites, for example:
* State of the properties' owners: The properties are all linked to the projects
* The impact on the properties defining the association Tool (0..1) - (*) Configuration

**Note**: The test projects use the extension `Tools/Properties/EtpMerge` to edit a few properties depending on a configuration.

## Properties
* The values of the properties SCALAR_* and LIST_* describe the test case: Del, new, modify...
* The test of properties independent of a configuration use the default properties of a project: `Description` and `Document` tabs.
* The project formalisms lacks of semantic, the tool considers:
  * A property is considered as scalar if it contains one and only one value in all the projects, for a single owner.
  * List values are not ordered.
