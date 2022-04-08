#!/usr/bin/env bash

set -euo pipefail

export SCHOLARREPLICAHOST=wbgrp-svc500.us.archive.org

cd /srv/fatcat_scholar/sitemap
/srv/fatcat_scholar/src/extra/sitemap/work_urls_query.sh
/srv/fatcat_scholar/src/extra/sitemap/access_urls_query.sh
/srv/fatcat_scholar/src/extra/sitemap/generate_sitemap_indices.py
scp *.txt *.xml $SCHOLARREPLICAHOST:/srv/fatcat_scholar/sitemap
