
<div align="center">
<img src="src/scholar/static/scholar-vaporwave-logo.png">
</div>

# Internet Archive Scholar

IA Scholar is an effort within the [Internet Archive](https://archive.org) to track, preserve, index, and serve scholarly articles.

Our focus is on [Open Access](https://en.wikipedia.org/wiki/Open_access) content that might otherwise disappear from the web, but we also focus on building an open bibliographic database of all scholarly content.

This is source code for [scholar.archive.org](https://scholar.archive.org), a
full-text web search interface over the 25+ million open research papers in the
Internet Archive.

All of the technical heavy lifting of harvesting, crawling, and metadata corrections are
handled by the [fatcat](https://fatcat.wiki)  service; this service is just a bare-bones, read-only
search interface. Unlike the basic fatcat.wiki search, this index allows
querying the full content of papers when available.


## Overview

This repository is fairly small and contains:

- `src/scholar/`: Python code for web service and indexing pipeline
- `src/scholar/templates/`: HTML template for web interface
- `tests/`: Python test files
- `proposals/`: design documentation and change proposals
- `data/`: empty directory for indexing pipeline

A data pipeline converts groups of one or more fatcat "release" entities
(grouped under a single "work" entity) into a single search index document.
Elasticsearch is used as the full-text search engine. A simple web interface
parses search requests and formats Elasticsearch results with highlights and
first-page thumbnails.

## Getting Started for Developers

You'll need `python3`. We test against 3.11; your mileage may vary with older pythons. Ensure that `pip` and `venv` modules are available (these need to be installed manually via `apt` on Debian).

Most tasks are run using a Makefile; `make help` will show all options.

Working on the indexing pipeline effectively requires internal access to the
Internet Archive cluster and services, though some contributions and bugfixes
are probably possible without staff access.

To install dependencies for the first time run:

    make dep

then run the tests (to ensure everything is working):

    make test

To start the web interface run:

    make serve

While developing the web interface, you will almost certainly need an example
database running locally. A docker-compose file in `extra/docker/` can be used
to run Elasticsearch 7.x locally. The `make dev-index` command will reset the
local index with the correct schema mapping, and index any intermediate files
in the `./data/` directory. We don't have an out-of-the-box solution for non-IA
staff at this step (yet).

After making changes to any user interface strings, the interface translation
file (".pot") needs to be updated with `make extract-i18n`. When these changes
are merged to master, the Weblate translation system will be updated
automatically.

This repository uses `ruff` for code formatting and `mypy` for type checking;
please run `make fmt` and `make lint` for submitting a pull request.


## Contributing

Software, copy-editing, translation, and other contributions to this repository
are welcome! For content and metadata corrections, or identifying new content
to include, the best place to start is the in [fatcat
repository](https://github.com/internetarchive/fatcat). Learn more in the
[fatcat guide](https://guide.fatcat.wiki). You can chat and ask questions on
[gitter.im/internetarchive/fatcat](https://gitter.im/internetarchive/fatcat).

Contributors in this project are asked to abide by our
[Code of Conduct](https://guide.fatcat.wiki/code_of_conduct.html).

The web interface is translated using the Weblate platform, at
[internetarchive/fatcat-scholar](https://hosted.weblate.org/projects/internetarchive/fatcat-scholar/)

The software license for this repository is Affero General Public License v3+
(APGL 3+), as described in the `LICENSE.md` file. We ask that you acknowledge
the license terms when making your first contribution.

For software developers, the "help wanted" tag in Github Issues is a way to
discover bugs and tasks that external folks could contribute to.
