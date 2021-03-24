

Can be multiple releases for each work:

- required: most canonical published version ("version of record", what would be cited)
    => or, most updated?
- optional: mostly openly accessible version
- optional: updated version
    => errata, corrected version, or retraction
- optional: fulltext indexed version
    => might be not the most updated, or no accessible


## Initial Plan

Index all fatcat works in catalog.

Always link to a born-digital copy if one is accessible.

Always link to a SIM microfilm copy if one is available.

Use best available fulltext for search. If structured, like TEI-XML, index the
body text separate from abstracts and references.


## Other Ideas

Do fulltext indexing at the granularity of pages, or some other segments of
text within articles (paragraphs, chapters, sections).

Fatcat already has all of Crossref, Pubmed, Arxiv, and several other
authoritative metadata sources. But today we are missing a good chunk of
content, particularly from institutional repositories and CS conferences (which
don't use identifiers). Also don't have good affiliation or citation count
coverage, and mixed/poor abstract coverage.

Could use Microsoft Academic Graph (MAG) metadata corpus (or similar) to
bootstrap with better metadata coverage.
