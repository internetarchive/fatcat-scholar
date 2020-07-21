
Run a partial ~5 million paper batch through:

    zcat /srv/fatcat_scholar/release_export.2019-07-07.5mil_fulltext.json.gz \
        | parallel -j8 --linebuffer --round-robin --pipe python -m fatcat_scholar.work_pipeline run_releases \
        | pv -l \
        | gzip > data/work_intermediate.5mil.json.gz
    => 5M 21:36:14 [64.3 /s]

    # runs about 70 works/sec with this parallelism => 1mil in 4hr, 5mil in 20hr
    # looks like seaweedfs is bottleneck?
    # tried stopping persist workers on seaweedfs and basically no change

    indexing to ES seems to take... an hour per million? or so. can check index
    monitoring to get better number

## Work Grouping

Plan for work-grouped expanded release dumps:

Have release identifier dump script include, and sort by, `work_id`. This will
definitely slow down that stage, unclear if too much. `work_id` is indexed.

Bulk dump script iterates and makes work batches of releases to dump, passes
Vec to worker threads. Worker threads pass back Vec of entities, then print all
of them (same work) sequentially.
