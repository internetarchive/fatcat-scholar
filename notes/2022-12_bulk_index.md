
Running through a full end-to-end re-indexing.


## Fatcat Metadata Dumps

Run following fatcat notes (elsewhere).

Download to working machine:

    export JOBDIR=/kubwa/fatcat/2022-11-24
    mkdir -p $JOBDIR
    cd $JOBDIR
    wget -c https://archive.org/download/fatcat_bulk_exports_2022-11-24/release_export_expanded.json.gz

## Microfilm

Working directory: `aitio:/fast/fatcat-scholar`. 

Pulled latest git (`00d80752b7d83ae5a165540fbad641ddfc78b5f3`), and ran `make
dep`.

Run:

    TODAY=2022-12-08 make issue-db

Then, the SIM dump job, in parallel:

    export JOBDIR=/kubwa/scholar/2022-12-08
    mkdir -p $JOBDIR
    pipenv shell
    python -m fatcat_scholar.sim_pipeline run_print_issues \
        | shuf \
        | parallel -j16 --colsep "\t" python -m fatcat_scholar.sim_pipeline run_fetch_issue {1} {2} \
        | pv -l \
        | pigz \
        > $JOBDIR/sim_intermediate.2022-12-08.json.gz
    => 45.4M 42:09:42 [ 298 /s]

TODO: there were some old publications that should not be included... gazetteer? registers?
    "Daily Gazetteer" (sim_daily-gazetteer)

## Works Bulk Fetch

First split up the release dump into chunks:

    export JOBDIR=/kubwa/scholar/2022-12-08
    mkdir -p $JOBDIR
    cd $JOBDIR
    zcat /kubwa/fatcat/2022-11-24/release_export_expanded.json.gz | split --lines 8000000 - release_export_expanded.split_ -d --additional-suffix .json
    => done

Note: more shards this time around (up to 23, not 21).

Starting the below commands on 2022-12-21.

    export JOBDIR=/kubwa/scholar/2022-12-08
    cd /fast/fatcat-scholar
    pipenv shell
    export TMPDIR=/sandcrawler-db/tmp
    # possibly re-export JOBDIR from above?

    # fetch
    set -u -o pipefail
    for SHARD in {00..23}; do
        cat $JOBDIR/release_export_expanded.split_$SHARD.json \
            | parallel -j8 --line-buffer --compress --tmpdir $TMPDIR --round-robin --pipe python -m fatcat_scholar.work_pipeline run_releases \
            | pv -l \
            | pigz \
            > $JOBDIR/fatcat_scholar_work_fulltext.split_$SHARD.json.gz.WIP \
            && mv $JOBDIR/fatcat_scholar_work_fulltext.split_$SHARD.json.gz.WIP $JOBDIR/fatcat_scholar_work_fulltext.split_$SHARD.json.gz
    done
