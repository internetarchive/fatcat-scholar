
Run a partial ~5 million paper batch through:

    zcat /srv/fatcat_scholar/release_export.2019-07-07.5mil_fulltext.json.gz \
        | parallel -j8 --line-buffer --round-robin --pipe python -m fatcat_scholar.work_pipeline run_releases \
        | pv -l \
        | gzip > data/work_intermediate.5mil.json.gz
    => 5M 21:36:14 [64.3 /s]

    # runs about 70 works/sec with this parallelism => 1mil in 4hr, 5mil in 20hr
    # looks like seaweedfs is bottleneck?
    # tried stopping persist workers on seaweedfs and basically no change

    indexing to ES seems to take... an hour per million? or so. can check index
    monitoring to get better number

## 2020-07-23 First Full Release Batch

Patched to skip fetching `pdftext`

Run full batch through (on aitio), expecting this to take on the order of a
week:

    zcat /fast/download/release_export_expanded.json.gz \
        | parallel -j8 --line-buffer --compress --round-robin --pipe python -m fatcat_scholar.work_pipeline run_releases \
        | pv -l \
        | gzip > /grande/snapshots/fatcat_scholar_work_fulltext.20200723.json.gz

Ah, this was running really slow because `MINIO_SECRET_KEY` was not set. Really
should replace `minio` python client library as we are now using seaweedfs!

Got an error:

    36.1M 15:29:38 [ 664 /s]
    parallel: Error: Output is incomplete. Cannot append to buffer file in /fast/tmp. Is the disk full?
    parallel: Error: Change $TMPDIR with --tmpdir or use --compress.
    Warning: unable to close filehandle properly: No space left on device during global destruction.

Might have been due to `/` filling up (not `/fast/tmp`)? Had gotten pretty far
in to processing. Restarted, will keep an eye on it.

To index, run from ES machine, as bnewbold:

    ssh aitio.us.archive.org cat /grande/snapshots/fatcat_scholar_work_fulltext.partial.20200723.json.gz \
    | gunzip \
    | sudo -u fatcat parallel -j8 --linebuffer --round-robin --pipe pipenv run python -m fatcat_scholar.transform run_transform \
    | esbulk -verbose -size 100 -id key -w 4 -index qa_scholar_fulltext_v01 -type _doc

Hrm, again:

    99.9M 56:04:41 [ 308 /s]
    parallel: Error: Output is incomplete. Cannot append to buffer file in /fast/tmp. Is the disk full?
    parallel: Error: Change $TMPDIR with --tmpdir or use --compress.

Confirmed that disk was full in that moment; frustrating as had checked in and
disk usage was low enough before, and data was flowing to /grande (large
spinning disk). Should be sufficient to move release dump to `/bigger` and
clear more space on `/fast` to do the full indexing.

    /dev/sdg1       917G  871G     0 100% /fast

    vs.

    /dev/sdg1       917G  442G  430G  51% /fast

    -rw-rw-r-- 1 bnewbold bnewbold  418G Jul 27 05:55 fatcat_scholar_work_fulltext.20200723.json.gz

Got to about 2/3 of full release dump. Current rough estimates for total
processing times:

    enrich 150 million releases: 80hr (3-4 days), 650 GByte on disk (gzip)
    transform and index 150 million releases: 55hr (2-3 days), 1.5 TByte on disk (?)

## ES Performance Iteration (2020-07-27)

- schema: switch abstracts from nested to simple array
- query: include fewer fields: just biblio (with boost; and maybe title) and "everything"
- query: use date-level granularity for time queries (may already do this?)
- set replica=0 (for now)
- set shards=12, to optimize *individual query* performance
    => if estimating 800 GByte index size, this is 60-70 GByte per shard
- set `index.codec=best_compression` to leverage CPU vs. disk I/O
- ensure transform output is sorted by key
    => <https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-disk-usage.html#_put_fields_in_the_same_order_in_documents>
- ensure number of cores is large
- return fewer results (15 vs. 25)
    => less highlighting
    => fewer thumbnails to catch

## Work Grouping

Plan for work-grouped expanded release dumps:

Have release identifier dump script include, and sort by, `work_id`. This will
definitely slow down that stage, unclear if too much. `work_id` is indexed.

Bulk dump script iterates and makes work batches of releases to dump, passes
Vec to worker threads. Worker threads pass back Vec of entities, then print all
of them (same work) sequentially.
