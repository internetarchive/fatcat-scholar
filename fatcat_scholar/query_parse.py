
"""
This file contains helpers for pre-parsing and transforming search query
strings. See the "basic query parsing" proposal doc for original motivation and
design details.
"""

import shlex


def _clean_token(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        return '"{}"'.format(raw)
    if len(raw.split()) > 1:
        # has whitespace, will get quoted
        return raw
    if "/" in raw or raw.endswith(":"):
        return '"{}"'.format(raw)
    return raw


def pre_parse_query(raw: str) -> str:
    """
    This method does some pre-parsing of raw query strings to prepare them for
    passing on as a elasticsearch query string query (which is really just the
    lucene query language).

    For exaple, it tries to handle trailing semi-colons (could be interpreted
    as a field filter) and slashes in words.
    """
    # if there is a fuzzy match, skip parse attempt
    # TODO: can we configure shlex to handle this?
    if '"~' in raw:
        return raw
    lex = shlex.shlex(raw, posix=False)
    lex.commenters = ''
    lex.whitespace_split = True
    tokens = list(map(_clean_token, list(lex)))
    print(list(tokens))
    return " ".join(tokens)


def test_pre_parse_query() -> None:
    assert pre_parse_query("blah blah blah") == "blah blah blah"
    assert pre_parse_query("is_oa:") == '"is_oa:"'
    assert pre_parse_query("is_oa: ") == '"is_oa:"'
    assert pre_parse_query("is_oa:1") == "is_oa:1"
    assert pre_parse_query("is_oa:*") == "is_oa:*"
    assert pre_parse_query("<xml>") == "<xml>"
    assert pre_parse_query(r"""some $\LaTeX$""") == r"some $\LaTeX$"
    assert pre_parse_query("N/A") == '"N/A"'
    assert pre_parse_query("a/B thing") == '"a/B" thing'
    assert pre_parse_query('"a/B thing"') == '"a/B thing"'
    assert pre_parse_query("Krämer") == "Krämer"
    assert (
        pre_parse_query("this (is my) paper: here are the results")
        == 'this (is my) "paper:" here are the results'
    )
    assert (
        pre_parse_query('"hello world" computing type:book')
        == '"hello world" computing type:book'
    )
    assert (
        pre_parse_query('"hello world" computing type:"chapter thing"')
        == '"hello world" computing type:"chapter thing"'
    )
    assert pre_parse_query('"foo bar"~4') == '"foo bar"~4'
    assert pre_parse_query('(title:foo OR title:bar)^1.5 (body:foo OR body:bar)') == '(title:foo OR title:bar)^1.5 (body:foo OR body:bar)'
    assert pre_parse_query('(title:"foo bar" AND body:"quick fox") OR title:fox') == '(title:"foo bar" AND body:"quick fox") OR title:fox'
    assert pre_parse_query('status:[400 TO 499] AND (extension:php OR extension:html)') == 'status:[400 TO 499] AND (extension:php OR extension:html)'
