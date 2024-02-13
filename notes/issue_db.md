
## Commands

    mkdir -p data
    ia search "collection:periodicals collection:sim_microfilm mediatype:collection" --itemlist | rg "^pub_" > data/sim_collections.tsv
    ia search "collection:periodicals collection:sim_microfilm mediatype:texts" --itemlist | rg "^sim_" > data/sim_items.tsv

    cat data/sim_collections.tsv | parallel -j4 ia metadata {} | jq . -c | pv -l > data/sim_collections.json
    cat data/sim_items.tsv | parallel -j8 ia metadata {} | jq . -c | pv -l > data/sim_items.json

    cat data/sim_collections.2020-05-15.json | pv -l | python -m scholar.issue_db load_pubs
    cat data/sim_items.2020-05-15.json | pv -l | python -m scholar.issue_db load_issues
    python -m scholar.issue_db load_counts
