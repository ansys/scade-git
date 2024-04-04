# Properties: Test Notes
## Goals
This test suite is used to ensure the properties `@STUDIO:TOOLCONF` and their values are properly merged/reconciled.

These properties have a hardcoded semantic for Studio. Their name is identical and the the first value determines the related tool. The other values are the IDs if the configurations applicable to this tool.

Thus:
* The key is `<name, values[0]>` instead of `<name, configuration.id>`.
* Before merging the values:
  * The remote's values must be reconciled with the IDs of the related local configurations, when exist.
  * The local's deleted configurations must shall value must be filtered regarding the deleted  configurations.

## Configurations
* The name of the configurations correspond to the changes done in local and remote versions.
