
Want to receive a continual stream of updates from both fatcat and SIM
scanning; index the updated content; and push into elasticsearch.


## Message Types

Scholar Update Request JSON
- `key`: str
- `type`: str
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
