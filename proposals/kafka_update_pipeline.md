
Want to receive a continual stream of updates from both fatcat and SIM
scanning; index the updated content; and push into elasticsearch.


## Filtering and Affordances

The `updated` and `fetched` timestamps are not immediately necessary or
implemented, but they can be used to filter updates. For example, after
re-loading from a build entity dump, could "roll back" update pipeline to only
fatcat (work) updates after the changelog index that the bulk dump is stamped
with.

At least in theory, the `fetched` timestamp could be used to prevent re-updates
of existing documents in the ES index.

The `doc_index_ts` timestamp in the ES index could be used in a future
fetch-and-reindex worker to select documents for re-indexing, or to delete
old/stale documents (eg, after SIM issue re-indexing if there were spurious
"page" type documents remaining).

## Message Types

Scholar Update Request JSON
- `key`: str - `type`: str
    - `fatcat_work`
    - `sim_issue`
- `updated`: datetime, UTC, of event resulting in this request
- `work_ident`: str (works)
- `fatcat_changelog`: int (works)
- `sim_item`: str (items)

"Heavy Intermediate" JSON (existing schema)
- key
- `fetched`: Optional[datetime], UTC, when this doc was collected

Scholar Fulltext ES JSON (existing schema)


## Kafka Topics

fatcat-ENV.work-ident-updates
    6x, long retention, key compaction
    key: doc ident
scholar-ENV.sim-updates
    6x, long retention, key compaction
    key: doc ident
scholar-ENV.update-docs
    12x, short retention (2 months?)
    key: doc ident

## Workers

scholar-fetch-docs-worker
    consumes fatcat and/or sim update requests, individually
    constructs heavy intermediate
    publishes to update-docs topic

scholar-index-docs-worker
    consumes updated "heavy intermediate" documents, in batches
    transforms to elasticsearch schema
    updates elasticsearch
