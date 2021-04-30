#!/usr/bin/env bash

set -e              # fail on error
set -u              # fail if variable not set in substitution
set -o pipefail     # fail if part of a '|' command fails

: ${1?' You you did not supply a date argument'}

# eg, 2020-08-19
DATE="$1"

# query for specific works; about 8.6 million circa 2021-04-29
fatcat-cli search scholar 'doc_type:work (fulltext.access_type:ia_file OR fulltext.access_type:wayback) (NOT biblio.arxiv_id:*) (NOT biblio.pmcid:*) (NOT biblio.publisher_type:big5) (year:<1926 OR tags:*)' --index-json --limit 0 \
    | pv -l \
    | jq .key -r \
    | tr '_' '/' \
    | awk '{print "https://scholar.archive.org/" $1}' \
    | split --lines 20000 - sitemap-works-$DATE- -d -a 5 --additional-suffix .txt

gzip sitemap-works-*.txt
