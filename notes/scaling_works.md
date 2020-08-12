
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

Failed again, due to null `release.extra` field.

    # 14919639 + 83111800 = 98031439
    ssh aitio.us.archive.org cat /grande/snapshots/fatcat_scholar_work_fulltext.20200723.json.gz     | gunzip   | tail -n +98031439  | sudo -u fatcat parallel -j8 --linebuffer --round-robin --pipe pipenv run python -m fatcat_scholar.transform run_transform     | esbulk -verbose -size 100 -id key -w 4 -index qa_scholar_fulltext_v01 -type _doc

SIM remote indexing command:

    # size before (approx): 743.4 GByte, 98031407 docs; 546G disk free
    ssh aitio.us.archive.org cat /bigger/scholar_old/sim_intermediate.2020-07-23.json.gz     | gunzip   | sudo -u fatcat parallel -j8 --linebuffer --round-robin --pipe pipenv run python -m fatcat_scholar.transform run_transform     | esbulk -verbose -size 100 -id key -w 4 -index qa_scholar_fulltext_v01 -type _doc
    => 1967593 docs in 2h8m32.549646403s at 255.116 docs/s with 4 workers
    # size after: 753.8gb 99926090 docs, 533G disk free

Trying dump again on AITIO, with alternative tmpdir:

    git log | head -n1
    commit 2f0874c84e71a02a10e21b03688593a4aa5ef426

    df -h /sandcrawler-db/
    Filesystem      Size  Used Avail Use% Mounted on
    /dev/sdf1       1.8T  684G  1.1T  40% /sandcrawler-db

    export TMPDIR=/sandcrawler-db/tmp
    zcat /fast/download/release_export_expanded.json.gz \
        | parallel -j8 --line-buffer --compress --round-robin --pipe python -m fatcat_scholar.work_pipeline run_releases \
        | pv -l \
        | gzip > /grande/snapshots/fatcat_scholar_work_fulltext.20200723_two.json.gz

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

## ES Permformance Profiling (2020-08-05)

Index size:

    green open scholar_fulltext_v01            uthJZJvSS-mlLIhZxrlVnA 12 0 102039078 578722 748.9gb 748.9gb

Unless otherwise mentioned, these are with default filters in place.

Baseline:

    {"query": {"bool": {"filter": [{"terms": {"type": ["article-journal", "paper-conference", "chapter"]}}, {"terms": {"access_type": ["wayback", "ia_file", "ia_sim"]}}], "must": [{"boosting": {"positive": {"bool": {"must": [{"query_string": {"query": "coffee", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["title^5", "biblio_all^3", "abstracts.body^2", "fulltext.body", "everything"]}}], "should": [{"terms": {"access_type": ["ia_sim", "ia_file", "wayback"]}}]}}, "negative": {"bool": {"should": [{"bool": {"must_not": [{"exists": {"field": "title"}}]}}, {"bool": {"must_not": [{"exists": {"field": "year"}}]}}, {"bool": {"must_not": [{"exists": {"field": "type"}}]}}, {"bool": {"must_not": [{"exists": {"field": "stage"}}]}}, {"bool": {"must_not": [{"exists": {"field": "biblio.container_ident"}}]}}]}}, "negative_boost": 0.5}}]}}, "collapse": {"field": "collapse_key", "inner_hits": {"name": "more_pages", "size": 0}}, "from": 0, "size": 15, "highlight": {"fields": {"abstracts.body": {"number_of_fragments": 2, "fragment_size": 300}, "fulltext.body": {"number_of_fragments": 2, "fragment_size": 300}, "fulltext.acknowledgment": {"number_of_fragments": 2, "fragment_size": 300}, "fulltext.annex": {"number_of_fragments": 2, "fragment_size": 300}}}}


    jenny durkin
    => 60 Hits in 1.3sec

    "looking at you kid"
    => 83 Hits in 6.6sec

    LIGO black hole
    => 2,440 Hits in 1.6sec

    "configuration that formed when the core of a rapidly rotating massive star collapsed"
    => 1 Hits in 8.0sec
    => requery: in 0.3sec

Disable everything, query only `biblio_all`:

    {"query": {"query_string": {"query": "coffee", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["biblio_all^3"]}}, "from": 0, "size": 15}

    newbold
    => 2,930 Hits in 0.12sec

    guardian galaxy
    => 15 Hits in 0.19sec

    *
    => 102,039,078 Hits in 0.86sec (same on repeat)

Query only `everything`:

    guardian galaxy
    => 1,456 Hits in 0.26sec

    avocado mexico
    => 3,407 Hits in 0.3sec, repeat in 0.017sec

    *
    => 102,039,078 Hits in 0.9sec (same on repeat)


Query all the fields with boosting:

    {"query": {"query_string": {"query": "coffee", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["title^5", "biblio_all^3", "abstracts.body^2", "fulltext.body", "everything"]}}, "from": 0, "size": 15}

    berlin population
    => 168,690 Hits in 0.93sec repeat in in 0.11sec

    internet archive
    => 115,139 Hits in 1.1sec

    *
    => 102,039,078 Hits in 4.1sec (same on repeat)

Query only "everything", add highlighting (default config):

    indiana human
    => 86,556 Hits in 0.34sec repeat in 0.04sec
    => scholar-qa: 86,358 Hits in 2.4sec, repeat in 0.47sec

    wikipedia
    => 73,806 Hits in 0.13sec

Query only "everything", no highlighting, basic filters:

    {"query": {"bool": {"filter": [{"terms": {"type": ["article-journal", "paper-conference", "chapter"]}}, {"terms": {"access_type": ["wayback", "ia_file", "ia_sim"]}}], "must": [{"query_string": {"query": "reddit", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["everything"]}}]}}, "from": 0, "size": 15}

    reddit
    => 5,608 Hits in 0.12sec

    "participate in this collaborative editorial process"
    => 1 Hits in 7.9sec, repeat in in 0.4sec
    scholar-qa: timeout (>10sec)

    "one if by land, two if by sea"
    => 20 Hits in 4.5sec

Query only "title", no highlighting, basic filters:

    "discontinuities and noise due to crosstalk"
    => 0 Hits in 0.24sec
    scholar-qa: 1 Hits in 4.7sec

Query only "everything", no highlighting, collapse key:

    greed
    => 35,941 Hits in 0.47sec

    bjog child
    => 6,616 Hits in 0.4sec 

Query only "everything", no highlighting, collapse key, boosting:

    blue
    => 2,407,966 Hits in 3.1sec
    scholar-qa: 2,407,967 Hits in 1.6sec

    distal fin tuna
    => 390 Hits in 0.61sec

    "greater speed made possible by the warm muscle"
    => 1 Hits in 1.2sec

Query "everything", highlight "everything", collapse key, boosting (default but
only "everything" match):

    NOTE: highlighting didn't work

    green
    => 2,742,004 Hits in 3.1sec, repeat in in 2.8sec

    "comprehensive framework for the influences"
    => 1 Hits in 3.1sec

    bivalve extinct
    => 6,631 Hits in 0.47sec

    redwood "big basin"
    => 69 Hits in 0.5sec

Default, except only search+highlight "fulltext.body":

    {"query": {"bool": {"filter": [{"terms": {"type": ["article-journal", "paper-conference", "chapter"]}}, {"terms": {"access_type": ["wayback", "ia_file", "ia_sim"]}}], "must": [{"boosting": {"positive": {"bool": {"must": [{"query_string": {"query": "coffee", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["fulltext.body"]}}], "should": [{"terms": {"access_type": ["ia_sim", "ia_file", "wayback"]}}]}}, "negative": {"bool": {"should": [{"bool": {"must_not": [{"exists": {"field": "title"}}]}}, {"bool": {"must_not": [{"exists": {"field": "year"}}]}}, {"bool": {"must_not": [{"exists": {"field": "type"}}]}}, {"bool": {"must_not": [{"exists": {"field": "stage"}}]}}, {"bool": {"must_not": [{"exists": {"field": "biblio.container_ident"}}]}}]}}, "negative_boost": 0.5}}]}}, "collapse": {"field": "collapse_key", "inner_hits": {"name": "more_pages", "size": 0}}, "from": 0, "size": 15, "highlight": {"fields": {"fulltext.body": {"number_of_fragments": 2, "fragment_size": 300}}}}

    radioactive fish eye yellow
    => 1,401 Hits in 0.84sec

    "Ground color yellowish pale, snout and mouth pale gray"
    => 1 Hits in 1.1sec

Back to baseline:

    "palace of the fine arts"
    => 26 Hits in 7.4sec

    john
    => 1,812,894 Hits in 3.1sec

Everything disabled, but fulltext query all the default fields:

    {"query": {"query_string": {"query": "john", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["title^5", "biblio_all^3", "abstracts.body^2", "fulltext.body", "everything"]}}, "from": 0, "size": 15}

    jane
    => 318,757 Hits in 0.29sec

    distress dolphin plant echo
    => 355 Hits in 1.5sec

    "Michael Longley's most recent collection of poems"
    => 1 Hits in 1.2sec

    aqua
    => 95,628 Hits in 0.27sec

Defaults, but query only "biblio_all":

    "global warming"
    => 2,712 Hits in 0.29sec

    pink
    => 1,805 Hits in 0.24sec

    *
    => 20,426,310 Hits in 7.5sec

    review
    => 795,060 Hits in 1.5sec

    "to be or not"
    => 319 Hits in 0.81sec

Simple filters, `biblio_all`, boosting disabled:

    {"query": {"bool": {"filter": [{"terms": {"type": ["article-journal", "paper-conference", "chapter"]}}, {"terms": {"access_type": ["wayback", "ia_file", "ia_sim"]}}], "must": [{"query_string": {"query": "coffee", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["biblio_all^3"]}}]}}, "collapse": {"field": "collapse_key", "inner_hits": {"name": "more_pages", "size": 0}}, "from": 0, "size": 15}

    open
    => 155,337 Hits in 0.31sec

    all
    => 40,880 Hits in 0.24sec

    the
    => 7,369,084 Hits in 0.75sec

Boosting disabled, query only `biblio_all`:

    "triangulations among all simple spherical ones can be seen to be"
    => 0 Hits in 0.6sec, again in 0.028sec

    "di Terminal Agribisnis (Holding Ground) Rancamaya Bogor"
    => 1 Hits in 0.21sec

    "to be or not"
    => 319 Hits in 0.042sec

Same as above, add boosting back in:

    {"query": {"bool": {"filter": [{"terms": {"type": ["article-journal", "paper-conference", "chapter"]}}, {"terms": {"access_type": ["wayback", "ia_file", "ia_sim"]}}], "must": [{"query_string": {"query": "the", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["biblio_all^3"]}}, {"boosting": {"positive": {"bool": {"must": [{"query_string": {"query": "the", "default_operator": "AND", "analyze_wildcard": true, "allow_leading_wildcard": false, "lenient": true, "quote_field_suffix": ".exact", "fields": ["biblio_all^3"]}}], "should": [{"terms": {"access_type": ["ia_sim", "ia_file", "wayback"]}}]}}, "negative": {"bool": {"should": [{"bool": {"must_not": [{"exists": {"field": "title"}}]}}, {"bool": {"must_not": [{"exists": {"field": "year"}}]}}, {"bool": {"must_not": [{"exists": {"field": "type"}}]}}, {"bool": {"must_not": [{"exists": {"field": "stage"}}]}}, {"bool": {"must_not": [{"exists": {"field": "biblio.container_ident"}}]}}]}}, "negative_boost": 0.5}}]}}, "collapse": {"field": "collapse_key", "inner_hits": {"name": "more_pages", "size": 0}}, "from": 0, "size": 15}

    the
    => 7,369,084 Hits in 5.3sec, repeat in 5.1sec

Removing `poor_metadata` fields:

    tree
    => 1,521,663 Hits in 2.3sec, again in 2.2sec

    all but one removed...
    tree
    => 1,521,663 Hits in in 1.0sec, again in in 0.84sec

    3/5 negative...
    tree
    => 1,521,663 Hits in 3.5sec

    no boosting...
    tree
    => 1,521,663 Hits in 0.2sec

Testing "rescore" (with collapse disabled; `window_size`=50):


    search = search.query(basic_fulltext)
    search = search.extra(
        rescore={
            'window_size': 100,
            "query": {
                "rescore_query": Q(
                    "boosting",
                    positive=Q("bool", must=basic_fulltext, should=[has_fulltext],),
                    negative=poor_metadata,
                    negative_boost=0.5,
                ).to_dict(),
            },
        }
    )

    green; access:everything (rescoring)
    => 331,653 Hits in 0.05sec, again in 0.053sec

    *; access:everything (rescoring)
    => 93,043,404 Hits in 1.2sec, again in 1.2sec

    green; access:everything (rescoring)
    => 331,653 Hits in 0.041sec, again in 0.038sec

    *; access:everything (no boost)
    => 93,043,404 Hits in 1.1sec, again in 1.2sec

    green; access:everything (boost query)
    => 331,653 Hits in 0.96sec< again in 0.95sec

    *; access:everything (boost query)
    => 93,043,404 Hits in 13sec


Other notes:

    counting all records, default filters ("*")
        scholar-qa: 20,426,296 Hits in 7.4sec
        svc097: 20,426,310 Hits in 8.6sec

    "to be or not to be" hamlet
        scholar-qa: timeout, then 768 Hits in 0.73sec
        svc097: 768 Hits in 2.5sec, then 0.86 sec

    "to be or not to be"
        svc98: 16sec

Speculative notes:

querying more fields definitely seems heavy. should try `require_field_match`
with highlighter. to allow query and highlight fields to be separate? or
perhaps even a separate highlighter query. query "everything", highlight
specific fields.

scoring/boosting large reponses (more than a few hundred thousand hits) seems
expensive. this include the trivial '*' query.

some fulltext phrase queries seem to always be expensive. look in to phrase
indexing, eg term n-grams? looks like simple `index_phrases` parameter is
sufficient for the basic case

not a performance thing, but should revisit schema and field storage to reduce
size. eg, are we storing "exact" separately from stemming? does that increase
size? is fulltext.body and everything redundant?


TL;DR:
- scoring large result set (with boost) is slow (eg, "*"), but not bad for smaller result sets
    => confirmed this makes a difference, but can't do collapse at same time
- phrase queries are expensive, especially against fulltext
- query/match multiple fields is also proportionately expensive

TODO:
x index tweaks: smaller number types (eg, for year)
    https://www.elastic.co/guide/en/elasticsearch/reference/current/number.html
    volume, issue, pages, contrib counts
x also sort and remove null keys when sending docs to ES
    => already done
x experiment with rescore for things like `has_fulltext` and metadata quality boost. with a large window?
x query on fewer fields and separate highlight fields from query fields (title, `biblio_all`, everything)
x consider not having `biblio_all.exact`
x enable `index_phrases` on at least `everything`, then reindex
    => start with ~1mil test batch
x consider not storing `everything` on disk at all, and maybe not `biblio_all` either (only use these for querying). some way to not make fulltext.body queryable?
- PROBLEM: can't do `collapse` and `rescore` together
    => try only a boolean query instead of boosting
        => at least superficially, no large difference
    x  special case "*" query and do no scoring, maybe even sort by `_doc`
        => huge difference for this specific query
    => could query twice: once with regular storing + collapse, but "halt
       after" short number of hits to reduce rescoring (?), and second time
       with no responses to get total count
    => could manually rescore in client code, just from the returned hits?

future questions:
- consider deserializing hit _source documents to pydantic objects (to avoid null field errors)
- how much of current disk usage is terms? will `index_phrase` make worse?
- do we need to store term offsets in indexes to make phrase queries faster/better, especially if the field is not stored?

Performance seems to have diverged between the two instances, not sure why.
Maybe some query terms just randomly are faster on one instance or the other?
Eg, "wood"

## 2020-08-07 Test Phrase Indexing

Indexing 1 million papers twice, with old and new schema, to check impact of
phrase indexing, in ES 7.x.

    release_export.2019-07-07.5mil_fulltext.json.gz

    git checkout 0c7a2ace5d7c5b357dd4afa708a07e3fa85849fd
    http put ":9200/qa_scholar_fulltext_0c7a2ace?include_type_name=true" < schema/scholar_fulltext.v01.json
    ssh aitio.us.archive.org cat /grande/snapshots/fatcat_scholar_work_fulltext.20200723_two.json.gz \
        | gunzip \
        | head -n1000000 \
        | sudo -u fatcat parallel -j8 --linebuffer --round-robin --pipe pipenv run python -m fatcat_scholar.transform run_transform \
        | esbulk -verbose -size 100 -id key -w 4 -index qa_scholar_fulltext_0c7a2ace -type _doc

    # master branch, phrase indexing
    git checkout 2c681e32756538c84b292cc95b623ee9758846a6
    http put ":9200/qa_scholar_fulltext_2c681e327?include_type_name=true" < schema/scholar_fulltext.v01.json
    ssh aitio.us.archive.org cat /grande/snapshots/fatcat_scholar_work_fulltext.20200723_two.json.gz \
        | gunzip \
        | head -n1000000 \
        | sudo -u fatcat parallel -j8 --linebuffer --round-robin --pipe pipenv run python -m fatcat_scholar.transform run_transform \
        | esbulk -verbose -size 100 -id key -w 4 -index qa_scholar_fulltext_2c681e327 -type _doc

    http get :9200/_cat/indices
    [...]
    green open qa_scholar_fulltext_0c7a2ace    BQ9tH5OZT0evFCXiIJMdUQ 12 0   1000000      0   6.7gb   6.7gb
    green open qa_scholar_fulltext_2c681e327   PgRMn5v-ReWzGlCTiP7b6g 12 0   1000000      0   9.5gb   9.5gb
    [...]

So phrase indexing is...42% larger index on disk, even with other changes to
reduce size. We will probably approach 2 TByte total index size.

    "to be or not to be"
    => qa_scholar_fulltext_0c7a2ace: 65 Hits in 0.2sec (after repetitions)
    => qa_scholar_fulltext_2c681e327: 65 Hits in 0.065sec

    to be or not to be
    => qa_scholar_fulltext_0c7a2ace: 87,586 Hits in 0.16sec
    => qa_scholar_fulltext_2c681e327: 87,590 Hits in 0.16sec

    "Besides all beneficial properties studied for various LAB, a special attention need to be pay on the possible cytotoxicity levels of the expressed bacteriocins"
    => qa_scholar_fulltext_0c7a2ace: 1 Hits in 0.076sec
    => qa_scholar_fulltext_2c681e327: 1 Hits in 0.055sec

    "insect swarm"
    => qa_scholar_fulltext_0c7a2ace: 4 Hits in 0.032sec
    => qa_scholar_fulltext_2c681e327: 4 Hits in 0.024sec

    "how to"
    => qa_scholar_fulltext_0c7a2ace: 15,761 Hits in 0.11sec
    => qa_scholar_fulltext_2c681e327: 15,763 Hits in 0.054sec

Sort of splitting hairs at this scale, but does seem like phrase indexing helps
with some queries. Seems worth at least trying with large/full index.

## 2020-08-07 Iterated Release Batch

Sharded indexing:

    zcat /fast/download/release_export_expanded.2020-08-05.json.gz | split --lines 25000000 - release_export_expanded.split_ -d --additional-suffix .json

    export TMPDIR=/sandcrawler-db/tmp
    for SHARD in {00..06}; do
        cat /bigger/scholar/release_export_expanded.split_$SHARD.json \
            | parallel -j8 --line-buffer --compress --round-robin --pipe python -m fatcat_scholar.work_pipeline run_releases \
            | pv -l \
            | pigz > /grande/snapshots/fatcat_scholar_work_fulltext.split_$SHARD.json.gz
    done

Record counts:

    24.7M 15:09:08 [ 452 /s]
    24.7M 16:11:22 [ 423 /s]
    24.7M 16:38:19 [ 412 /s]
    24.7M 17:29:46 [ 392 /s]
    24.7M 14:55:53 [ 459 /s]
    24.7M 15:02:49 [ 456 /s]
    2M 1:10:36 [ 472 /s]

Have made transform code changes, now at git rev 7603dd0ade23e22197acd1fd1d35962c314cf797.

Transform and index, on svc097 machine:

    ssh aitio.us.archive.org cat /grande/snapshots/fatcat_scholar_work_fulltext.split_*.json.gz \
    | gunzip \
    | head -n2000000 \
    | sudo -u fatcat parallel -j8 --linebuffer --round-robin --pipe pipenv run python -m fatcat_scholar.transform run_transform \
    | esbulk -verbose -size 100 -id key -w 4 -index scholar_fulltext_v01 -type _doc

Derp, got a batch-size error. Let's try even smaller for the full batch:

    ssh aitio.us.archive.org cat /grande/snapshots/fatcat_scholar_work_fulltext.split_*.json.gz \
    | gunzip \
    | sudo -u fatcat parallel -j8 --linebuffer --round-robin --pipe pipenv run python -m fatcat_scholar.transform run_transform \
    | esbulk -verbose -size 50 -id key -w 4 -index scholar_fulltext_v01 -type _doc

