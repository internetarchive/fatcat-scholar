
## High-Level

- operate on an entire item
- check against issue DB and/or fatcat search
    => if there is fatcat work-level metadata for this issue, skip
- fetch collection-level (journal) metadata
- iterate through djvu text file:
    => convert to simple text
    => filter out non-research pages using quick heuristics
    => try looking up "real" page number from OCR work (in item metadata)
- generate "heavy" intermediate schema (per valid page):
    => fatcat container metadata
    => ia collection (journal) metadata
    => item metadata
    => page fulltext and any metadata

- transform "heavy" intermediates to ES schema

## Implementation

Existing tools and libraries:

- internetarchive python tool to fetch files and item metadata
- fatcat API client for container metadata lookup

New tools or libraries needed:

- issue DB or use fatcat search index to count releases by volume/issue
- djvu XML parser
