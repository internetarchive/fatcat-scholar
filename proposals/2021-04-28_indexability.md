
subject: work-in-progress

Persistent Landing Pages, Access URLs, Sitemaps
===============================================

This is a proposal to start hosting persistent landing pages (for "work"
entities) and access redirect URLs on the scholar.archive.org domain.
Additionally, to create bulk sitemaps linking to these resources.

The initial motivation for these features are to enable indexing, aggregation,
and linking to preservation content by large academic search engines (like
Google Scholar, Microsoft Academic, and lens.org), as well as simple linking
from platforms like Wikipedia. All of these may, for various reasons, prefer
linking directly to PDF files, and to have have links on a *.archive.org (as
opposed to fatcat.wiki).


# Work Landing Pages

New URL endpoint:

    /work/<ident>

Work landing pages will summarize bibliographic metadata about the work, list
versions ("releases") and list access options. The landing pages will include
bibliographic metadata summarized in HTML tags for the "primary" release.


In the future, these pages could be host to additional features or sub-pages
(new endpoints), such as:

- citation graph lists or visualizations
- alternative reading interface
- content previews


## Design Notes

The `citation_pdf_url` metadata tag will only link to a PDF file hosted on a
*.archive.org domain (aka, archive.org files or web.archive.org web-archived
files), via the access redirect URLs mentioned below. At least initially, only
PDF files which correspond to the "primary" version of the work will be
included. Eg, if there is a published release, a file manifestation of that
release will be linked, not earlier pre-print or accepted manuscript versions.
This behavior may change at some point to include "green" access links from the
"work" landing page.

The `citation_pdf_url` tag should contain an absolute URL, not a relative URL.

Alternatively, we could have landing pages only for "releases" (versions), like
already exist on fatcat.wiki. This would make the decision about which files to
link to simpler.

However, to date scholar.archive.org as a product/service has taken the
approach of simplifying the fatcat.wiki data model in the interest of
usability, and will probably continue with that approach here.

Landing pages will be rendered from a simple, single "GET" request to the same
elasticsearch backend index; no new backing services (eg, api.fatcat.wiki) are
introduced.

# Access Redirect URLs

Some academic search engines require a `citation_pdf_url` link from the same
domain as the landing page, with an optional HTTP redirect.

New URL endpoint:

    /access-redirect/<sha1>.pdf

Requests to such URLs will redirect (HTTP 302) to an *.archive.org access
location of the exact file (by sha1), if known.

It is likely that in the future `.xml` and `.epub` access redirect links would
be added in the same format. Unclear what the scheme would be for HTML content
(SHA-1 of the "primary" HTML document? or wayback timestamp and URL?).

This URL structure was chosen to reduce confusion that the file might be served
from scholar.archive.org itself ("redirect"); to indicate the filetype
expected; and to encode information about which resource is being linked to
("content addressible").


### Design Notes

An alternative would have been to scope the URL below the work itself, eg:

    /work/<ident>/access-redirect/<sha1>.pdf

Such URLs would be quite long.

These redirects are implemented by querying the same scholar elasticsearch
backend index, querying for fulltext access with the matching file SHA-1, and
using the `access_url` returned.


# Sitemap

The sitemap setup will be copied from fatcat.wiki. The new resources (URLs)
will include:

    /robots.txt - updated to include sitemap references
    /sitemap.xml - basic generic list of pages (homepage, about, userguide)
    /sitemap-index-works.xml - XML file pointing to many sub-sitemap files; includes lastmod metadata
    /sitemap-works-YYYY-MM-DD-NNNNN.txt - series of timestamped "simple" sitemaps (URL list files)

Only works for which there is an appropriate fulltext access URL 

The sitemap links from robots.txt should be absolute URLs, not relative URLs.
