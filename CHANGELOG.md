
# Change Log

## [1.2] - 2021-8-17
- Fixe the issue when turn nested JSON object into nested C structure.
- Fix the duplicated function name issue.
  This issue is caused by the identical Redfish property name defined in
  the different schemas.
- Fixes the issue of removing "CS" from the property name accidentally if
  there is the "CS" pattern in the property name.
- Update EDK2 auto-generated files.
- Add AUTHORS.md, CHANGELOG.md and LICENSE.md.
- Verified on schema2020.4 release.

## [1.1] - 2019-6-13
- Support empty property (e.g. "properties": {})

## [1.0] - 2018-9-25
- Initial version

