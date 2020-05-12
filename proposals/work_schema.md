
## Top-Level

- type: _doc
- key: keyword
- key_type: keyword (work or page)
- `work_id`
- biblio: obj
- fulltext: obj
- sim: obj
- abstracts: nested
    body
    lang
- releases: nested (TBD)
- access
- tags: array of keywords

TODO:
- summary fields to index "everything" into?

## Biblio

Mostly matches existing `fatcat_release` schema.

- `release_id`
- `release_revision`
- `title`
- `subtitle`
- `original_title`
- `release_date`
- `release_year`
- `withdrawn_status`
- `language`
- `country_code`
- `volume` (etc)
- `volume_int` (etc)
- `first_page`
- `first_page_int`
- `pages`
- `doi` etc
- `number` (etc)

NEW:
- `preservation_status`

[etc]

- `license_slug`
- `publisher` (etc)
- `container_name` (etc)
- `container_id`
- `container_issnl`
- `container_issn` (array)
- `contrib_names`
- `affiliations`
- `creator_ids`

## Fulltext

- `status`: web, sim, shadow
- `body`
- `lang`
- `file_mimetype`
- `file_sha1`
- `file_id`
- `thumbnail_url`

## Abstracts

Nested object with:

- body
- lang

For prototyping, perhaps just make it an object with `body` as an array.

Only index one abstract per language.

## SIM (Microfilm)

Enough details to construct a link or do a lookup or whatever. Note that might
be doing CDL status lookups on SERP pages.

Also pass-through archive.org metadata here (collection-level and item-level)

## Access

Start with obj, but maybe later nested?

- `status`: direct, cdl, repository, publisher, loginwall, paywall, etc
- `mimetype`
- `access_url`
- `file_url`
- `file_id`
- `release_id`

