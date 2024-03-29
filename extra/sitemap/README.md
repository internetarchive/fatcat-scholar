
## HOWTO: Update

Requires [fatcat-cli](https://gitlab.com/bnewbold/fatcat-cli) and `jq`
installed. Run these commands on a production machine.

    cd /srv/fatcat_scholar/sitemap
    /srv/fatcat_scholar/src/extra/sitemap/work_urls_query.sh
    /srv/fatcat_scholar/src/extra/sitemap/access_urls_query.sh
    /srv/fatcat_scholar/src/extra/sitemap/generate_sitemap_indices.py

Then copy to alternate/replica machine:

    scp *.txt *.xml $SCHOLARREPLICAHOST:/srv/fatcat_scholar/sitemap

## Background

Google has a limit of 50k lines / 10 MByte for text sitemap files, and 50K
lines / 50 MByte for XML site map files. Google Scholar has indicated a smaller
20k URL / 5 MB limit.

## Resources

Google sitemap verifier: https://support.google.com/webmasters/answer/7451001
