from elasticsearch_dsl import Search

from fatcat_scholar.search import FulltextQuery, apply_filters


def test_apply_filters() -> None:
    search = Search()
    query = FulltextQuery()
    apply_filters(search, query)
