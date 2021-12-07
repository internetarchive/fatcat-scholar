
SIM digitization is mostly complete, looking at starting to (re)index.

Around 2021-12-01, re-ran build of issue DB, with filters like
`(pub_type:"Scholarly Journals" OR pub_type:"Historical Journals" OR
pub_type:"Law Journals")`:

    ia search 'collection:periodicals collection:sim_microfilm mediatype:collection (pub_type:"Scholarly Journals" OR pub_type:"Historical Journals" OR pub_type:"Law Journals")' -n
    # 7947

    ia search 'collection:periodicals collection:sim_microfilm mediatype:texts !noindex:true (pub_type:"Scholarly Journals" OR pub_type:"Historical Journals" OR pub_type:"Law Journals")' -n
    # 849593

If filters are relaxed, and all microfilm included, could be:

    ia search 'collection:periodicals collection:sim_microfilm mediatype:collection' -n
    # 13590

    ia search 'collection:periodicals collection:sim_microfilm mediatype:texts' -n
    # 1870482

    ia search 'collection:periodicals collection:sim_microfilm mediatype:texts (pub_type:"Scholarly Journals" OR pub_type:"Historical Journals" OR pub_type:"Law Journals")' -n
    # 849599

With the tighter filters (initially), looking at:

    select count(*) from sim_pub;
    7902

    select count(*) from sim_pub where container_ident is not null;
    5973

    select count(*) from sim_pub where issn is not null;
    6107

    select pub_type, count(*) from sim_pub where issn is null group by pub_type;
    pub_type        count(*)
    Historical Journals     1568
    Law Journals    11
    Scholarly Journals      216

    select count(*) from sim_issue;
    667073

    select count(*) from sim_issue where release_count is null;
    373921

    select count(*) from sim_issue where release_count = 0;
    262125

    select sum(release_count) from sim_issue;
    534609

    select sum(release_count) from release_counts;
    # PREVIOUSLY: 397,602
    # 8,231,201

What container types do we have in fatcat?

    zcat container_export.json.gz | rg "sim_pubid" | jq .extra.ia.sim.pub_type | sort | uniq -c | sort -nr
       7135 "Scholarly Journals"
       2572 "Trade Journals"
       1325 "Magazines"
        187 "Law Journals"
        171 "Government Documents"
         21 "Historical Journals"

How many releases are we expecting to match?

    fatcat-cli search containers any_ia_sim:true --count
    # 11965

    fatcat-cli search release in_ia_sim:true --count
    # 22,470,053

    fatcat-cli search release in_ia_sim:true container_id:* --count
    # 22,470,053 (100%)

    fatcat-cli search release in_ia_sim:true container_id:* year:* --count
    # 22,470,053

    fatcat-cli search release in_ia_sim:true container_id:* volume:* --count
    # 20,498,018

    fatcat-cli search release in_ia_sim:true container_id:* year:* volume:* --count
    # 20,498,018

    fatcat-cli search release in_ia_sim:true container_id:* volume:* issue:* --count
    # 7,311,684

    fatcat-cli search release in_ia_sim:true container_id:* volume:* issue:* pages:* --count
    # 7,112,117

    fatcat-cli search release in_ia_sim:true container_id:* volume:* pages:* --count
    # 20,017,423

    fatcat-cli search release 'in_ia_sim:true container_id:* !issue:*' --count
    # 14,737,140

    fatcat-cli search release 'in_ia_sim:true container_id:* !issue:* doi:* doi_registrar:crossref' --count
    # 14,620,485

    fatcat-cli search release 'in_ia_sim:true container_id:* !issue:* doi:* doi_registrar:crossref in_ia:false' --count
    # 12,320,127

    fatcat-cli search scholar doc_type:work access_type:ia_sim --count
    # 66162

    fatcat-cli search scholar doc_type:sim_page --count
    # 10,448,586

The large majority of releases which *might* get included, are not. Missing an
issue number is the single largest category; almost all are Crossref DOIs; the
large majority are not in IA otherwise.

One conclusion from this is that updating fatcat with additional
volume/issue/page metadata (if available) could be valuable. Or, in the
short-term, copying this information from crossref metadata in the
fatcat-scholar pipeline would make sense.

There is still an open question of why so few of the ~7 million fatcat releases
which *should* match to SIM, are failing to. Is it because they have not been
processed? Or the issues are getting filtered?

----

Queries against chocula DB, to gauge possible breakdown by SIM `pub_type`:

    SELECT * FROM directory
    WHERE
        slug = 'sim'
        AND extra LIKE '%"Scholarly Journals"%'
    LIMIT 5;

    SELECT journal.issnl, journal.release_count
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND extra LIKE '%"Scholarly Journals"%'
        AND journal.issnl IS NOT NULL
    LIMIT 5;

    SELECT SUM(journal.release_count)
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND journal.issnl IS NOT NULL;
    # 40,579,513

    SELECT SUM(journal.release_count - journal.preserved_count)
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND journal.issnl IS NOT NULL;
    # 2,692,023

    SELECT SUM(journal.release_count)
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND extra LIKE '%"Scholarly Journals"%'
        AND journal.issnl IS NOT NULL;
    # 39,020,833

    SELECT SUM(journal.release_count)
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND extra LIKE '%"Trade Journals"%'
        AND journal.issnl IS NOT NULL;
    # 755,367

    SELECT SUM(journal.release_count)
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND extra LIKE '%"Magazines"%'
        AND journal.issnl IS NOT NULL;
    # 487,197

    SELECT SUM(journal.release_count)
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND extra LIKE '%"Law Journals"%'
        AND journal.issnl IS NOT NULL;
    # 78,519

    SELECT SUM(journal.release_count)
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND extra LIKE '%"Government Documents"%'
        AND journal.issnl IS NOT NULL;
    # 30,786

    SELECT SUM(journal.release_count)
    FROM directory
    LEFT JOIN journal ON journal.issnl = directory.issnl
    WHERE
        slug = 'sim'
        AND extra LIKE '%"Historical Journals"%'
        AND journal.issnl IS NOT NULL;
    # 206,811

To summarize counts, remembering that these apply to entire runs of journals
with any coverage in the SIM collection (not by year/volume/issue matching):

    Scholarly:      39,020,833
    Trade:             755,367
    Magazines:         487,197
    Law:                78,519
    Government:         30,786
    Historical:        206,811
    Total:          40,579,513
    "Unpreserved":   2,692,023

The TL;DR is that almost everything is "Scholarly Journals", with very little
"Law" or "Historical" coverage.

----

Experimented with a handful of examples, and it seems like newer-processed
(tesseract) SIM does work with the existing pipeline (eg, the djvu files still
work).

----

How many pages exist now, and how many do we expect to index?

    SELECT SUM(last_page-first_page) FROM sim_issue;
    # 83,504,593

    SELECT SUM(last_page-first_page) FROM sim_issue WHERE (release_count IS NULL OR release_count < 5);
    SELECT SUM(last_page-first_page) FROM sim_issue WHERE (release_count IS NULL OR release_count < 5);
    # 75,907,903

    fatcat-cli search scholar doc_type:sim_page --count
    # 10,448,586

Large increase, but not too wild.

Generate issues metadata:

    # in pipenv shell
    python -m fatcat_scholar.sim_pipeline run_print_issues \
        | shuf \
        | parallel -j16 --colsep "\t" python -m fatcat_scholar.sim_pipeline run_fetch_issue {1} {2} \
        | pv -l \
        | pigz \
        > /kubwa/scholar/2021-12-01/sim_intermediate.2021-12-01.json.gz
    # 20.2M 13:44:18 [ 408 /s]

If this runs at 300 pages/sec (aggregate), it will take 3-4 days to extract all
pages.

Huh, got only a fraction of what was expected. Lots of errors on individual
issues, but that should be fine/expected.

Let's try a sub-sample of 1000 issues, after also adding some print statements:

    python -m fatcat_scholar.sim_pipeline run_print_issues \
        | shuf -n1000 \
        | parallel -j16 --colsep "\t" python -m fatcat_scholar.sim_pipeline run_fetch_issue {1} {2} \
        | pv -l \
        | pigz \
        > /kubwa/scholar/2021-12-01/sim_intermediate.2021-12-01.1k_issues.json.gz
    # 76.1k 0:03:34 [ 354 /s]

    # issue without leaf numbers: sim_journal-of-organizational-and-end-user-computing_1989-1992_1-4_cumulative-index
    # issue without leaf numbers: sim_review-of-english-studies_1965_16_contents_0

How many issues are attempted?

    python -m fatcat_scholar.sim_pipeline run_print_issues \
        | wc -l
    # 268,707

    SELECT COUNT(*) FROM sim_issue LEFT JOIN sim_pub ON sim_issue.sim_pubid = sim_pub.sim_pubid WHERE sim_issue.release_count < 5;
    # 268,707

    SELECT COUNT(*) FROM sim_issue LEFT JOIN sim_pub ON sim_issue.sim_pubid = sim_pub.sim_pubid WHERE sim_issue.release_count < 5 OR sim_issue.release_count IS NULL;
    # 642,015

    SELECT COUNT(*) FROM sim_issue LEFT JOIN sim_pub ON sim_issue.sim_pubid = sim_pub.sim_pubid WHERE sim_issue.release_count < 100 OR sim_issue.release_count IS NULL;
    # 667,023

Not including the `OR sim_issue.release_count IS NULL` was a bug.

Also, should skip additional suffixes:
- _contents_0
- _cumulative-index
- _index-contents

With those changes:

    python -m fatcat_scholar.sim_pipeline run_print_issues \
        | wc -l
    # 627,304

Ok, start the dump again:

    mv /kubwa/scholar/2021-12-01/sim_intermediate.2021-12-01.json.gz /kubwa/scholar/2021-12-01/sim_intermediate.2021-12-01.partial.json.gz

    python -m fatcat_scholar.sim_pipeline run_print_issues \
        | shuf \
        | parallel -j16 --colsep "\t" python -m fatcat_scholar.sim_pipeline run_fetch_issue {1} {2} \
        | pv -l \
        | pigz \
        > /kubwa/scholar/2021-12-01/sim_intermediate.2021-12-01.json.gz
    # 43.5M 34:20:45 [ 351 /s]

Huh. Why is this still only 43 out of 75 million pages? Because of blank pages,
or something else? Should add counters to indexing process, write out a
per-issue log of counts and status. But good progress for now, I guess.
