
"""
Helpers to make elasticsearch queries.
"""

import json
import datetime

import elasticsearch
from elasticsearch_dsl import Search, Q
from dynaconf import settings


def generic_search_execute(search, limit=25, offset=0, deep_page_limit=2000):

    # Sanity checks
    if limit > 100:
        limit = 100
    if offset < 0:
        offset = 0
    if offset > deep_page_limit:
        # Avoid deep paging problem.
        offset = deep_page_limit

    search = search[int(offset):int(offset)+int(limit)]

    try:
        resp = search.execute()
    except elasticsearch.exceptions.RequestError as e:
        # this is a "user" error
        print("elasticsearch 400: " + str(e.info))
        #flash("Search query failed to parse; you might need to use quotes.<p><code>{}: {}</code>".format(e.error, e.info['error']['root_cause'][0]['reason']))
        # XXX: abort(e.status_code)
        raise Exception()
    except elasticsearch.exceptions.TransportError as e:
        # all other errors
        print("elasticsearch non-200 status code: {}".format(e.info))
        # XXX: abort(e.status_code)
        raise Exception()

    # convert from objects to python dicts
    results = []
    for h in resp:
        r = h._d_
        #print(json.dumps(h.meta._d_, indent=2))
        r['_highlights'] = []
        if 'highlight' in dir(h.meta):
            highlights = h.meta.highlight._d_
            for k in highlights:
                r['_highlights'] += highlights[k]
        results.append(r)

    for h in results:
        # Handle surrogate strings that elasticsearch returns sometimes,
        # probably due to mangled data processing in some pipeline.
        # "Crimes against Unicode"; production workaround
        for key in h:
            if type(h[key]) is str:
                h[key] = h[key].encode('utf8', 'ignore').decode('utf8')

    return {
        "count_returned": len(results),
        "count_found": int(resp.hits.total),
        "results": results,
        "offset": offset,
        "limit": limit,
        "deep_page_limit": deep_page_limit,
        "query_time_ms": int(resp.took),
    }

def do_fulltext_search(q, limit=25, offset=0, filter_time=None, filter_type=None):

    # Convert raw DOIs to DOI queries
    if len(q.split()) == 1 and q.startswith("10.") and q.count("/") >= 1:
        q = 'doi:"{}"'.format(q)

    es_client = elasticsearch.Elasticsearch(settings.ELASTICSEARCH_BACKEND)
    search = Search(using=es_client, index=settings.ELASTICSEARCH_FULLTEXT_INDEX)

    # type filters
    if filter_type == "papers":
        search = search.filter("terms", release_type=[ "article-journal", "paper-conference", "chapter", ])
    elif filter_type == "reports":
        search = search.filter("terms", release_type=[ "report", "standard", ])
    elif filter_type == "datasets":
        search = search.filter("terms", release_type=[ "dataset", "software", ])
    elif filter_type == "everything" or filter_type == None:
        pass
    else:
        # XXX: abort(400)
        raise Exception()

    # time filters
    if filter_time == "past_week":
        week_ago_date = str(datetime.date.today() - datetime.timedelta(days=7))
        search = search.filter("range", release_date=dict(gte=week_ago_date))
    elif filter_time == "this_year":
        search = search.filter("term", release_year=datetime.date.today().year)
    elif filter_time == "since_2000":
        search = search.filter("range", release_year=dict(gte=2000))
    elif filter_time == "before_1925":
        search = search.filter("range", release_year=dict(lte=1924))
    elif filter_time == "all_time" or filter_time == None:
        pass
    else:
        # XXX: abort(400)
        raise Exception()

    search = search.query(
        'query_string',
        query=q,
        default_operator="AND",
        analyze_wildcard=True,
        lenient=True,
        fields=[
            "everything",
            "abstract",
            "fulltext.body",
            "fulltext.annex",
        ],
    )
    search = search.highlight(
        "abstract",
        "fulltext.body",
        "fulltext.annex",
        number_of_fragments=3,
        fragment_size=150,
    )

    resp = generic_search_execute(search, offset=offset)

    for h in resp['results']:
        # Ensure 'contrib_names' is a list, not a single string
        if type(h['contrib_names']) is not list:
            h['contrib_names'] = [h['contrib_names'], ]
        h['contrib_names'] = [name.encode('utf8', 'ignore').decode('utf8') for name in h['contrib_names']]

    resp["query"] = { "q": q }
    return resp
