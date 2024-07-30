import json
from urllib.parse import urlencode
from fuzzycat.simple import FuzzyReleaseMatchResult, Status, Reason
import scholar.fatcat.web

# TODO /release/{ident}/references

def test_reference_match(client, fcclient, mocker, entities):
    # on GET we render an empty form
    rv = client.get("/fatcat/reference/match")
    assert rv.status_code == 200
    assert "Matched Releases" not in rv.text
    assert "Parsed Citation" not in rv.text

    # POST with submit_type=parse

    mocker.patch("scholar.fatcat.web.grobid_api_process_citation")
    scholar.fatcat.web.grobid_api_process_citation.return_value = '<biblStruct >\n\t<analytic>\n\t\t<title level="a" type="main">The winograd schema challenge</title>\n\t\t<author>\n\t\t\t<persName><forename type="first">Hector</forename><surname>Levesque</surname></persName>\n\t\t</author>\n\t\t<author>\n\t\t\t<persName><forename type="first">Ernest</forename><surname>Davis</surname></persName>\n\t\t</author>\n\t\t<author>\n\t\t\t<persName><forename type="first">Leora</forename><surname>Morgen- Stern</surname></persName>\n\t\t</author>\n\t</analytic>\n\t<monogr>\n\t\t<title level="m">Thirteenth International Conference on the Princi- ples of Knowledge Representation and Reasoning</title>\n\t\t\t\t<imprint>\n\t\t\t<date type="published" when="2012">2012</date>\n\t\t</imprint>\n\t</monogr>\n</biblStruct>\n'

    matches = [FuzzyReleaseMatchResult(
        status=Status.AMBIGUOUS, reason=Reason.UNKNOWN, release=entities["release"])]
    mocker.patch("scholar.fatcat.web.close_fuzzy_release_matches")
    scholar.fatcat.web.close_fuzzy_release_matches.return_value = matches

    fcclient.get_release.return_value=entities["release"]

    rv = client.post(
            "/fatcat/reference/match",
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

    # POST with submit_type=match

    mocker.patch("scholar.fatcat.web.close_fuzzy_biblio_matches")
    scholar.fatcat.web.close_fuzzy_biblio_matches.return_value = matches

    rv = client.post(
            "/fatcat/reference/match",
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

def test_reference_match_json(client, fcclient, mocker, entities):
    matches = [FuzzyReleaseMatchResult(
        status=Status.AMBIGUOUS, reason=Reason.UNKNOWN, release=entities["release"])]
    mocker.patch("scholar.fatcat.web.close_fuzzy_biblio_matches")
    scholar.fatcat.web.close_fuzzy_biblio_matches.return_value = matches
    fcclient.get_release.return_value=entities["release"]

    q = urlencode({"submit_type": "match",
                  "raw_citation": "Hector+Levesque,+Ernest+Davis,+and+Leora+Morgen-+stern.+2012.+The+winograd+schema+challenge.+In+Thirteenth+International+Conference+on+the+Princi-+ples+of+Knowledge+Representation+and+Reasoning.",
                  "title": "The+winograd+schema+challenge",
                  "first_author": "Hector+Levesque",
                  "journal": "Thirteenth+International+Conference+on+the+Princi-+ples+of+Knowledge+Representation+and+Reasoning",
                  "year": "2012",
                  "volume": "",
                  "issue":"",
                  "pages": ""})

    rv = client.get("/fatcat/reference/match.json?"+q)
    assert rv.status_code == 200
    payload = rv.json()
    assert len(payload) == 1
    assert payload[0]["status"] == "ambiguous"
    assert payload[0]["reason"] == "unknown"
    assert payload[0]["release"]["title"] == "steel and lace"

def test_release_refs_json(client, fcclient, entities, es, es_resps):
    es.side_effect = [
        (200, {}, json.dumps(es_resps["release_refs_in"])),
        (200, {}, json.dumps(es_resps["release_refs_out"])),
        (200, {}, json.dumps(es_resps["release_refs_empty"])),
    ]
    fcclient.get_release.return_value=entities["release"]
    ident = entities["release"].ident

    rv = client.get(f"/fatcat/release/{ident}/refs-in.json")

    assert rv.status_code == 200
    payload = rv.json()
    assert payload["count_returned"] == 9
    assert len(payload["result_refs"]) == 9

    rv = client.get(f"/fatcat/release/{ident}/refs-out.json")

    assert rv.status_code == 200
    payload = rv.json()
    assert payload["count_returned"] == 30
    assert len(payload["result_refs"]) == 30

    # same ident, just simulating empty
    rv = client.get(f"/fatcat/release/{ident}/refs-out.json")

    assert rv.status_code == 200
    payload = rv.json()
    assert payload["count_returned"] == 0
    assert len(payload["result_refs"]) == 0

def test_release_refs_html(client, fcclient, entities, es, es_resps):
    es.side_effect = [
        (200, {}, json.dumps(es_resps["release_refs_in"])),
        (200, {}, json.dumps(es_resps["release_refs_out"])),
        (200, {}, json.dumps(es_resps["release_refs_empty"])),
    ]
    fcclient.get_release.return_value=entities["release"]
    ident = entities["release"].ident

    rv = client.get(f"/fatcat/release/{ident}/refs-in")

    assert rv.status_code == 200
    assert "Showing 1 - 9 of 69 references" in rv.text

    rv = client.get(f"/fatcat/release/{ident}/refs-out")

    assert rv.status_code == 200
    assert "Showing 1 - 30 of 34 references" in rv.text

    # same ident, simulating empty
    rv = client.get(f"/fatcat/release/{ident}/refs-out")

    assert rv.status_code == 200
    assert "Showing 0 references" in rv.text

def test_openlibrary_refs(client, fcclient, entities, es, es_resps):
    es.side_effect = [
        (200, {}, json.dumps(es_resps["release_refs_in"])),
        (200, {}, json.dumps(es_resps["release_refs_empty"])),
        (200, {}, json.dumps(es_resps["release_refs_in"])),
        (200, {}, json.dumps(es_resps["release_refs_empty"])),
    ]
    fcclient.get_release.return_value=entities["release"]

    rv = client.get("/fatcat/openlibrary/OL123W/refs-in")
    assert rv.status_code == 200
    assert "Showing 1 - 9 of 69 references" in rv.text

    # simulating empty
    rv = client.get("/fatcat/openlibrary/OL123W/refs-in")
    assert rv.status_code == 200
    assert "Showing 0 references" in rv.text

    rv = client.get("/fatcat/openlibrary/OL123W/refs-in.json")

    assert rv.status_code == 200
    payload = rv.json()
    assert payload["count_returned"] == 9
    assert len(payload["result_refs"]) == 9

    # simulating empty
    rv = client.get("/fatcat/openlibrary/OL123W/refs-in.json")

    assert rv.status_code == 200
    payload = rv.json()
    assert payload["count_returned"] == 0
    assert len(payload["result_refs"]) == 0

def test_wikipedia_refs(client, fcclient, entities, es, es_resps):
    es.side_effect = [
        (200, {}, json.dumps(es_resps["release_refs_out"])),
        (200, {}, json.dumps(es_resps["release_refs_empty"])),
        (200, {}, json.dumps(es_resps["release_refs_out"])),
        (200, {}, json.dumps(es_resps["release_refs_empty"])),
    ]
    fcclient.get_release.return_value=entities["release"]

    rv = client.get("/fatcat/wikipedia/en:foobar/refs-out")
    assert rv.status_code == 200
    assert "Showing 1 - 30 of 34 references" in rv.text

    # simulating empty
    rv = client.get("/fatcat/wikipedia/en:foobar/refs-out")
    assert rv.status_code == 200
    assert "Showing 0 references" in rv.text

    rv = client.get("/fatcat/wikipedia/en:foobar/refs-out.json")

    assert rv.status_code == 200
    payload = rv.json()
    assert payload["count_returned"] == 30
    assert len(payload["result_refs"]) == 30

    # simulating empty
    rv = client.get("/fatcat/wikipedia/en:foobar/refs-out.json")

    assert rv.status_code == 200
    payload = rv.json()
    assert payload["count_returned"] == 0
    assert len(payload["result_refs"]) == 0
