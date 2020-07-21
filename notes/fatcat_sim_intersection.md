
investigate how many fatcat releases match to SIM:
- dump archive.org SIM collection-level metadata
- dump archive.org issue item-level metadata
- releases with: in_sim, volume, issue, page, year (month?)
    => 22m   in_ia_sim
    =>  1.1m in_ia_sim preservation:none
    => 20m   in_ia_sim volume
    => 20m   in_ia_sim volume year
    => 19m   in_ia_sim volume pages
    =>  5m   in_ia_sim volume year date
    =>  7m   in_ia_sim volume issue
    =>  7m   in_ia_sim volume issue pages
    =>  6m   in_ia_sim volume issue pages first_page
    =>  5.3m in_ia_sim volume issue pages first_page in_web:false
    =>  0.7m in_ia_sim volume issue pages first_page preservation:none
    =>  2.5m in_ia_sim volume issue pages first_page date
- how many (any?) SIM journals with no fatcat container
    total: 14860
    missing-issn: 2863
    no-match: 554
    -> 3417./ 14860 = 23%
- how many SIM journals/issues/years with ~no fatcat releases?
    as of 2020-07-21: of 212 pubids (with scanned issues so far), 129 have any fatcat releases (60%)

at least some (release_jpruczlec5gsjpbc2cbvwedsdy) have updated crossref
metadata with issue numbers


## 2020-07-20

Categories of interesction:

- fatcat catalog record and in SIM corpus: have good metadata, could
  potentially extract just pages (for fulltext search) and link directly to
  access
    => at least 22m records; 18.4m no known public fulltext
    => at least 6m with enough metadata to match; 5.3m no known public fulltext
        => TODO: how many of this 16m metadata gap can be fixed by finding better metadata?
    => SIM digitized yet?
    => TODO: estimate at issue level

    example:
        "The Savings Gained From Participation in Health Promotion Programs for Medicare Beneficiaries"
        https://fatcat.wiki/release/hp7jsz2cfnc3dgepk7oxj7kvjm
        https://archive.org/details/sim_journal-of-occupational-and-environmental-medicine_2006-11_48_11/page/1125
        https://scholar-qa.archive.org/search?q=%22responses+to+the+hra+or+from+data+gathered%22

- SIM corpus paper, no fatcat catalog record
    => TODO: estimate from issue count/ratio

- fatcat catalog record, and fulltext, no SIM paper

Current scholar.archive.org behavior is to use fatcat metadata to create a
work-level document (with multiple pages) if possible. If not, the entire issue
is issue is split into page-level documents.

TODO: only "count" paper/records which have enough metadata to actually link
(eg, volume, issue, pages), not just any `in_ia_sim`.

#### SQL Queries

    select count(*) from sim_pub;
    => 212

    select count(distinct sim_pubid) from release_counts;
    => 129

    select count(*) from sim_issue;
    => 78301

    select count(*) from sim_issue left join release_counts on sim_issue.year = release_counts.year and sim_issue.sim_pubid = release_counts.sim_pubid and sim_issue.volume = release_counts.volume where release_counts.sim_pubid is not null and release_counts.release_count > 0;
    => 218

    select count(*) from sim_issue left join release_counts on sim_issue.year = release_counts.year and sim_issue.sim_pubid = release_counts.sim_pubid and sim_issue.volume = release_counts.volume where release_counts.sim_pubid is not null and release_counts.release_count >= 3;
    => 179

    select count(*) from sim_issue left join release_counts on sim_issue.year = release_counts.year and sim_issue.sim_pubid = release_counts.sim_pubid and sim_issue.volume = release_counts.volume where release_counts.sim_pubid is not null and release_counts.release_count >= 10;
    => 166

    select sum(release_count) from release_counts;
    => 9968

    select sum(release_count) from release_counts where release_count >= 3;
    => 9940

    select count(*) from (select 1 from sim_issue group by sim_pubid, volume);
    => 6405

    select count(*) from (select sim_pubid, SUM(release_count) as release_count from release_counts group by sim_pubid);
    => 129

    select count(*) from (select sim_pubid, SUM(release_count) as release_count from release_counts group by sim_pubid) where release_count >= 10;
    => 86

    select count(*) from (select sim_pubid, SUM(release_count) as release_count from release_counts group by sim_pubid) where release_count >= 100;
    => 27

