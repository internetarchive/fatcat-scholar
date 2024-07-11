#!/bin/bash

# This script sets up a subset of the scholar_fulltext ES index for use in QA.
# The motivation for this was the desire to test deleting things from scholar's
# index without affecting it in production.
#
# For now, the index is created using whatever documents match the search term
# "foobar" in the prod index. At time of writing this results in a tiny index
# of about 600 documents. Obviously if the prod collection changes it could
# lead to changes in the QA index so these documents should not be considered
# stable. They are for manual testing.

# TODO should this go in ansible?

eshost="https://search.qa.fatcat.wiki"
iname="qa_scholar_fulltext"
schema="../schema/scholar_fulltext.v01.json"

echo "deleting any old qa index..."
curl -sXDELETE $eshost/$iname
echo
echo
echo "creating new qa index..."
curl -sXPUT $eshost/$iname -H'Content-Type: application/json' -d@$schema
echo 
echo
echo "do reindex..."
curl -sXPOST $eshost/_reindex -H'Content-Type: application/json' -d'{"source":{"index":"scholar_fulltext_v01_20211208", "query":{"query_string": {"query": "foobar"}}},"dest":{"index":"'$iname'"}}'
