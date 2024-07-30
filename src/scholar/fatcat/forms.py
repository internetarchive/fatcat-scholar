from typing import Any, Dict

from fastapi import Request
from starlette_wtf import StarletteForm
from wtforms import (
        SelectField,
        StringField,
        TextAreaField,
        validators,
)

class ReferenceMatchForm(StarletteForm):
    submit_type = SelectField(
        "submit_type", [validators.DataRequired()], choices=["parse", "match"]
    )

    # The empty string defaults are required to match the behavior in the old
    # fatcat flask app. Without them fields get a None value; this resulted in
    # different results when passed through to ElasticSearch.

    raw_citation = TextAreaField("Citation String", render_kw={"rows": "3"}, default="")

    title = StringField("Title", default="")
    journal = StringField("Journal or Conference", default="")
    first_author = StringField("First Author", default="")
    # author_names = StringField("Author Names")
    # year = IntegerField('Year Released',
    #    [validators.Optional(True), valid_year])
    year = StringField("Year Released", default="")
    date = StringField("Date Released", default="")
    volume = StringField("Volume", default="")
    issue = StringField("Issue", default="")
    pages = StringField("Pages", default="")
    publisher = StringField("Publisher", default="")
    doi = StringField("DOI", default="")
    pmid = StringField("PubMed Identifier", default="")
    arxiv_id = StringField("arxiv.org Identifier", default="")
    release_type = StringField("Release Type", default="")
    release_stage = StringField("Release Stage", default="")

    @staticmethod
    def from_grobid_parse(
            request: Request,
            parse_dict: Dict[str, Any], raw_citation: str
    ) -> "ReferenceMatchForm":
        """
        Initializes form from GROBID extraction
        """
        rmf = ReferenceMatchForm(request)
        rmf.raw_citation.data = raw_citation

        direct_fields = ["title", "journal", "volume", "issue", "pages"]
        for k in direct_fields:
            if parse_dict.get(k):
                a = getattr(rmf, k)
                a.data = parse_dict[k]

        date = parse_dict.get("date")
        if date and len(date) >= 4 and date[0:4].isdigit():
            rmf.year.data = int(date[0:4])

        if parse_dict.get("authors"):
            rmf.first_author.data = parse_dict["authors"][0].get("name")

        return rmf

