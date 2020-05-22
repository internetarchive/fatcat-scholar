
"""
Helpers to make elasticsearch queries.
"""

import sys
import json
from gettext import gettext
import datetime
import elasticsearch
from pydantic import BaseModel
from dynaconf import settings
from dataclasses import dataclass
from elasticsearch_dsl import Search, Q
from typing import List, Dict, Tuple, Optional, Any, Sequence

# i18n note: the use of gettext below doesn't actually do the translation here,
# it just ensures that the strings are caught by babel for translation later

class FulltextQuery(BaseModel):
    q: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None
    filter_time: Optional[str] = None
    filter_type: Optional[str] = None
    filter_availability: Optional[str] = None
    sort_order: Optional[str] = None
    time_options: Any = {
        "label": gettext("Release Date"),
        "slug": "filter_time",
        "default": "all_time",
        "list": [
            {"label": gettext("All Time"), "slug": "all_time"},
            {"label": gettext("Past Week"), "slug": "past_week"},
            {"label": gettext("Past Year"), "slug": "past_year"},
            {"label": gettext("Since 2000"), "slug": "since_2000"},
            {"label": gettext("Before 1925"), "slug": "before_1925"},
        ],
    }
    type_options: Any = {
        "label": gettext("Resource Type"),
        "slug": "filter_type",
        "default": "papers",
        "list": [
            {"label": gettext("Papers"), "slug": "papers"},
            {"label": gettext("Reports"), "slug": "reports"},
            {"label": gettext("Datasets"), "slug": "datasets"},
            {"label": gettext("Everything"), "slug": "everything"},
        ],
    }
    availability_options: Any = {
        "label": gettext("Availability"),
        "slug": "filter_availability",
        "default": "everything",
        "list": [
            {"label": gettext("Everything"), "slug": "everything"},
            {"label": gettext("Fulltext"), "slug": "fulltext"},
            {"label": gettext("Open Access"), "slug": "oa"},
        ],
    }
    sort_options: Any = {
        "label": gettext("Sort Order"),
        "slug": "sort_order",
        "default": "relevancy",
        "list": [
            {"label": gettext("All Time"), "slug": "relevancy"},
            {"label": gettext("Recent First"), "slug": "time_desc"},
            {"label": gettext("Oldest First"), "slug": "time_asc"},
        ],
    }


class FulltextHits(BaseModel):
    count_returned: int
    count_found: int
    offset: int
    limit: int
    deep_page_limit: int
    query_time_ms: int 
    results: List[Any]


def do_fulltext_search(query: FulltextQuery, deep_page_limit: int = 2000) -> FulltextHits:

    es_client = elasticsearch.Elasticsearch(settings.ELASTICSEARCH_BACKEND)
    search = Search(using=es_client, index=settings.ELASTICSEARCH_FULLTEXT_INDEX)

    # Convert raw DOIs to DOI queries
    if len(query.q.split()) == 1 and query.q.startswith("10.") and query.q.count("/") >= 1:
        search = search.filter("terms", doi=query.q)
        query.q = "*"

    # type filters
    if query.filter_type == "papers":
        search = search.filter("terms", type=[ "article-journal", "paper-conference", "chapter", ])
    elif query.filter_type == "reports":
        search = search.filter("terms", type=[ "report", "standard", ])
    elif query.filter_type == "datasets":
        search = search.filter("terms", type=[ "dataset", "software", ])
    elif query.filter_type == "everything" or query.filter_type == None:
        pass
    else:
        raise ValueError(f"Unknown 'filter_type' parameter value: '{query.filter_type}'")

    # time filters
    if query.filter_time == "past_week":
        week_ago_date = str(datetime.date.today() - datetime.timedelta(days=7))
        search = search.filter("range", date=dict(gte=week_ago_date))
    elif query.filter_time == "past_year":
        # (date in the past year) or (year is this year)
        # the later to catch papers which don't have release_date defined
        year_ago_date = str(datetime.date.today() - datetime.timedelta(days=365))
        this_year = datetime.date.today().year
        search = search.filter(Q("range", date=dict(gte=year_ago_date)) | Q("term", year=this_year))
    elif query.filter_time == "since_2000":
        search = search.filter("range", year=dict(gte=2000))
    elif query.filter_time == "before_1925":
        search = search.filter("range", year=dict(lt=1925))
    elif query.filter_time == "all_time" or query.filter_time == None:
        pass
    else:
        raise ValueError(f"Unknown 'filter_time' parameter value: '{query.filter_time}'")

    # we combined several queries to improve scoring.

    # this query use the fancy built-in query string parser
    basic_fulltext = Q(
        'query_string',
        query=query.q,
        default_operator="AND",
        analyze_wildcard=True,
        allow_leading_wildcard=False,
        lenient=True,
        fields=[
            "title^5",
            "biblio_all^3",
            "abstracts_all^2",
            "everything",
        ],
    )
    has_fulltext = Q(
        'terms',
        access_type=["ia_sim", "ia_file", "wayback"],
    )
    poor_metadata = Q(
        'bool',
        should=[
            # if these fields aren't set, metadata is poor. The more that do
            # not exist, the stronger the signal.
            Q("bool", must_not=Q("exists", field="title")),
            Q("bool", must_not=Q("exists", field="year")),
            Q("bool", must_not=Q("exists", field="type")),
            Q("bool", must_not=Q("exists", field="stage")),
        ],
    )

    search = search.query(
        "boosting",
        positive=Q(
            "bool",
            must=basic_fulltext,
            should=[has_fulltext],
        ),
        negative=poor_metadata,
        negative_boost=0.5,
    )
    search = search.highlight(
        "abstracts_all",
        "fulltext.body",
        "fulltext.annex",
        number_of_fragments=2,
        fragment_size=300,
    )

    # sort order
    if query.sort_order == "time_asc":
        search = search.sort("year", "date")
    elif query.sort_order == "time_desc":
        search = search.sort("-year", "-date")
    elif query.sort_order == "relevancy" or query.sort_order == None:
        pass
    else:
        raise ValueError(f"Unknown 'sort_order' parameter value: '{query.sort_order}'")

    # Sanity checks
    limit = min((int(query.limit or 25), 100))
    offset = max((int(query.offset or 0), 0))
    if offset > deep_page_limit:
        # Avoid deep paging problem.
        offset = deep_page_limit

    search = search[offset:offset+limit]

    try:
        resp = search.execute()
    except elasticsearch.exceptions.RequestError as e:
        # this is a "user" error
        print("elasticsearch 400: " + str(e.info), file=sys.stderr)
        if e.info.get('error', {}).get('root_cause', {}):
            raise ValueError(str(e.info['error']['root_cause'][0].get('reason')))
        else:
            raise ValueError(str(e.info))
    except elasticsearch.exceptions.TransportError as e:
        # all other errors
        print("elasticsearch non-200 status code: {}".format(e.info), file=sys.stderr)
        raise IOError(str(e.info))

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

    return FulltextHits(
        count_returned=len(results),
        count_found=int(resp.hits.total),
        offset=offset,
        limit=limit,
        deep_page_limit=deep_page_limit,
        query_time_ms=int(resp.took),
        results=results,
    )
