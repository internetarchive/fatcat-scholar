
# CHANGELOG

Notable technical changes to the code base and schemas will be recorded here.

See also:

- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [0.2.6] - 2024-02-13

This is a big release though it lacks any functional changes; it's a general repository refresh and update.

### Added

- Outstanding weblate translation commits
- `make audit` for checking dependencies for security patches
- `make freeze` for generating requirements files

### Changed

- Upgrade to python 3.11
- Upgraded key dependencies
- Remove some unused dependencies
- Replaced `Pipefile` with a `pyproject.toml`
- Replaced `pipenv` with `pip` + `pip-compile`
- Replace pylint, flake8, black, and isort with ruff

## [0.2.1] - 2023-01-04

This is a roll-up release of many, many small improvements over the years. No
specific large recent changes.

### Added

- added Farsi/Persian (fa) translation
- added Italian (it) translation
- added Dutch (nl) translation
- added Portuguese (pt) translation
- added Korean (ko) translation
- work landing pages
- sitemaps (eg, sitemap.xml and work sitemaps linked from robots.txt)
- "access-redirect" URLs for PDF access
- RSS feeds of search results

### Changed

- parsed queries do not clobber user input (search box)
- internals: switch from `grobid2json` file `grobid_tei_xml` library

### Fixed

- web HTML template escaping, due to jinja2/async issue


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
