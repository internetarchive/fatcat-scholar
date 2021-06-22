#!/usr/bin/env bash

set -e              # fail on error
set -u              # fail if variable not set in substitution
set -o pipefail     # fail if part of a '|' command fails


# query for specific works; about 8.6 million circa 2021-04-29
# NOTE: filter out 12-digit access URLs (vs. 14-digit)
fatcat-cli search scholar 'doc_type:work (fulltext.access_type:ia_file OR fulltext.access_type:wayback) (NOT biblio.arxiv_id:*) (NOT biblio.pmcid:*) ((NOT biblio.publisher_type:big5) OR year:<1926 OR tags:oa)' --index-json --limit 0 \
    | jq -c 'select(.biblio.release_ident == .fulltext.release_ident)' \
    | rg -v '^null' \
    | rg -v 'web.archive.org/web/\d{12}/' \
    | jq .key -r \
    | tr '_' '/' \
    | awk '{print "https://scholar.archive.org/" $1}' \
    | pv -l \
    | split --lines 20000 - sitemap-works- -d -a 5 --additional-suffix .txt
