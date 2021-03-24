
# CHANGELOG

Notable technical changes to the code base and schemas will be recorded here.

See also:

- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

### Added

### Changed

### Fixed

## [0.2.0] - 2021-03-23

This version roughly corresponds to the official launch of of the service (on
the https://scholar.archive.org domain) in March 2021.

### Added

- added Russian (ru) translation (thanks @artem.ru!)
- added Norwegian Bokmål (nb) translation (thanks kingu!)
- added Croatian (hr) translation (thanks milotype!)
- citation pop-up feature (web)
- basic citation parsing to reduce query syntax errors
- citation parse-and-fuzzy-match feature
- optional goatcounter analytics

### Changed

- updated dynaconf dependency to version 3 (thanks @rochabruno)
- update required python version to 3.8
- major changes to search result page
- rewrote help page

### Fixed

- many i18n/localization bugs
- several mobile/responsive bugs

## [0.1.0] - 2020-10-01

First tagged release, and start of notable change tracking.
