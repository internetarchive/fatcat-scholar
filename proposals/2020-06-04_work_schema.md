
## Top-Level

- type: `_doc` (aka, no type, `include_type_name=false`)
- key: keyword (same as `_id`)
- `collapse_key`: work ident, or SIM issue item (for collapsing/grouping search hits)
- `doc_type`: keyword (work or page)
- `doc_index_ts`: timestamp when document indexed
- `work_ident`: fatcat work ident (optional)

- `biblio`: obj
- `fulltext`: obj
- `ia_sim`: obj
- `abstracts`: nested
    body
    lang
- `releases`: nested (TBD)
- `access`
- `tags`: array of keywords

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
- `container_wikidata_qid`
- `issns` (array)
- `contrib_names`
- `affiliations`
- `creator_ids`

TODO: should all external identifiers go under `releases` instead of `biblio`? Or some duplicated?

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

- `issue_item`: str
- `pub_collection`: str
- `sim_pubid`: str
- `first_page`: str


Also pass-through archive.org metadata here (collection-level and item-level)

## Access

Start with obj, but maybe later nested?

- `status`: direct, cdl, repository, publisher, loginwall, paywall, etc
- `mimetype`
- `access_url`
- `file_url`
- `file_id`
- `release_id`

