
Single domain (TBD, but eg <https://scholar.archive.org>) will host a web
search interface. May also expose APIs on this host, or might use a separate
host for that.

Content would not be hosted on this domain; all fulltext copies would be linked
to elsewhere.

Style (eg, colors, font?) would be similar to <https://archive.org>, but may or
may not have regular top bar (<https://web.archive.org> has this). There would
be no "write" or "modify" features on this site at all: users would not need to
log in. Metadata updates and features would all redirect to archive.org or
fatcat.wiki.


## Design and Features

Will try to hew most closely to Pubmed in style, layout, and features.

Only a single search interface (no separate "advanced" page). Custom query
parser.

Filtering and sort via controls under search box. A button opens a box with
more settings. If these are persisted at all, only via cookies or local
storage.

## URL Structure

All pages can be prefixed with a two-character language specifier. Default
(with no prefix) is english.

`/`: homepage, single-sentance, large search box, quick stats and info

`/about`: about

`/help`: FAQ?

`/help/search`: advanced query tips

`/search`: query and results page


## More Ideas

Things we *could* do, but maybe *shouldn't*:

- journal-level metadata and summary. Could just link to fatcat.


## APIs

Might also expose as public APIs on that domain:

- search
- citation matching
- save-paper-now


## Implementation

For first iteration, going to use:

- python3.7
- elasticsearch-dsl from python and page-load-per-query (not single-page-app)
- fastapi (web framework)
- jinja2 (HTML templating)
- babel (i18n)
- semantic-ui (CSS)
- minimal or no javascript
