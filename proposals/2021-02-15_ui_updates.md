
status: partially-implemented

This documents a series of changes made in early 2021, before launch.

## Default URLs and Access (done)

Replace current access link under thumbnail with a box that can expand to show
more access options: domain, rel, filetype, release (version), maybe wayback date

Labels over the thumbnail should show type (PDF, HTML), and maybe release stage
(if different from primary release).

"Blue Links" for each hit should change, eg:

- if arxiv, arxiv.org
- elif PMID or PMCID, PubMed
- elif DOI, publisher (or whatever; follow the DOI)
- elif microfilm, go to access
- else fatcat landing page

What about: JSTOR, DOAJ


## Version Display (done)

Instead of showing a grid, could keep style similar to what already exits: the
single line of year/venue/status, then a line of identifiers in green (done)


## Query Behaviors

- "fail less": re-write more queries, potentially after ES has already returned a failure (done)
- change the default of only showing fulltext hits?


## Tooltips/Extras (done)

- show date when mouse-over year field
- have some link of container name to fatcat container page


## Clickable Queries

Allow search filters by clicking on: author, year, container

Filters should simply be added to current query string. Not sure how to implement.


## Responsive Design (done)

There is a window width (tablet?) where we keep a fixed column width with
margins, which results in small thumbnails. (done)
