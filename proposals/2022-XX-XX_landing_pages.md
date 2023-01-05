
status: planning

Work Langing Page Refactor
==========================

New features:

- policy pages
    => or could just add these to The Guide?
    /help/authors
        updated works
        removing content
        correcting metadata
    /help/publishers
        inclusion
        take downs


- work landing pages
    /work/<work_id>
        => access options
        => versions
        => abstract
        => metadata: biblio, etc
        => links elsewhere
        => citation formats
    /work/<work_id>.json
    /work/<work_id>/citation.txt?style=apa
    /work/<work_id>/citation.json?style=apa
- citation graph
    /work/<work_id>/refs-in
    /work/<work_id>/refs-out

- venue
    => just pull from fatcat API?
    => search?
- venue: browse
    /venue/<container_id>/browse
        => like SERP page, but show top bar? thumbnails?


## Other UI/UX details

- align width of top bar to that of footer and search
- remove beta labels (top bar, homepage)
