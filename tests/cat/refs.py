# TODO references / reference matching

# TODO /reference/match.json
# TODO /release/{ident}/refs-out.json
# TODO /release/{ident}/refs-in.json
# TODO /release/{ident}/refs-out
# TODO /release/{ident}/refs-in
# TODO /openlibrary/OL{id_num}W/refs-in
# TODO /openlibrary/OL{id_num}W/refs-in.json
# TODO /wikipedia/{wiki_lang}:{wiki_article}/refs-out
# TODO /wikipedia/{wiki_lang}:{wiki_article}/refs-out.json

import datetime
from fuzzycat.simple import FuzzyReleaseMatchResult, Status, Reason
import scholar.cat.web

# TODO /reference/match (POST, GET)
def test_reference_match(client, fcclient, mocker, entities, es, es_resps):
    # on GET we render an empty form
    rv = client.get("/cat/reference/match")
    assert rv.status_code == 200
    assert "Matched Releases" not in rv.text
    assert "Parsed Citation" not in rv.text

    mocker.patch("scholar.cat.web.grobid_api_process_citation")
    scholar.cat.web.grobid_api_process_citation.return_value = '<biblStruct >\n\t<analytic>\n\t\t<title level="a" type="main">The winograd schema challenge</title>\n\t\t<author>\n\t\t\t<persName><forename type="first">Hector</forename><surname>Levesque</surname></persName>\n\t\t</author>\n\t\t<author>\n\t\t\t<persName><forename type="first">Ernest</forename><surname>Davis</surname></persName>\n\t\t</author>\n\t\t<author>\n\t\t\t<persName><forename type="first">Leora</forename><surname>Morgen- Stern</surname></persName>\n\t\t</author>\n\t</analytic>\n\t<monogr>\n\t\t<title level="m">Thirteenth International Conference on the Princi- ples of Knowledge Representation and Reasoning</title>\n\t\t\t\t<imprint>\n\t\t\t<date type="published" when="2012">2012</date>\n\t\t</imprint>\n\t</monogr>\n</biblStruct>\n'

    matches = [FuzzyReleaseMatchResult(
        status=Status.AMBIGUOUS, reason=Reason.UNKNOWN, release=entities["release"])]
    mocker.patch("scholar.cat.web.close_fuzzy_release_matches")
    scholar.cat.web.close_fuzzy_release_matches.return_value = matches

    fcclient.get_release.return_value=entities["release"]

    rv = client.post(
            "/cat/reference/match",
            data={"submit_type": "parse",
                  "raw_citation": "Hector+Levesque,+Ernest+Davis,+and+Leora+Morgen-+stern.+2012.+The+winograd+schema+challenge.+In+Thirteenth+International+Conference+on+the+Princi-+ples+of+Knowledge+Representation+and+Reasoning."})

    assert "Parsed Citation" in rv.text
    assert "<code>authors</code>" in rv.text
    assert "&#39;name&#39;: &#39;Hector Levesque&#39;" in rv.text
    assert "<code>date</code>" in rv.text
    assert "<code>2012</code>" in rv.text
    assert "<code>journal</code>" in rv.text
    assert "<code>Thirteenth International Conference on the Princi- ples of Knowledge Representation and Reasoning</code>" in rv.text
    assert '<code>title</code>' in rv.text
    assert "<code>The winograd schema challenge</code>" in rv.text

    assert "<i>No matches found</i>" not in rv.text
    assert "AMBIGUOUS" in rv.text
    assert "UNKNOWN" in rv.text
    assert "steel and lace" in rv.text
    assert "no fulltext" in rv.text

    mocker.patch("scholar.cat.web.close_fuzzy_biblio_matches")
    scholar.cat.web.close_fuzzy_biblio_matches.return_value = matches

    rv = client.post(
            "/cat/reference/match",
            data={"submit_type": "match",
                  "raw_citation": "Hector+Levesque,+Ernest+Davis,+and+Leora+Morgen-+stern.+2012.+The+winograd+schema+challenge.+In+Thirteenth+International+Conference+on+the+Princi-+ples+of+Knowledge+Representation+and+Reasoning.",
                  "title": "The+winograd+schema+challenge",
                  "first_author": "Hector+Levesque",
                  "journal": "Thirteenth+International+Conference+on+the+Princi-+ples+of+Knowledge+Representation+and+Reasoning",
                  "year": "2012",
                  "volume": "",
                  "issue":"",
                  "pages": ""})

    assert "Parsed Citation" not in rv.text
    assert "<i>No matches found</i>" not in rv.text
    assert "AMBIGUOUS" in rv.text
    assert "UNKNOWN" in rv.text
    assert "steel and lace" in rv.text
    assert "no fulltext" in rv.text
