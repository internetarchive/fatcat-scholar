
subject: implemented

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

New URL endpoints:

    /work/<ident>/access/wayback/<original-url>
    /work/<ident>/access/ia_file/<archive-item>/<file-path>

Requests to such URLs will redirect (HTTP 302) to an *.archive.org access
location of the exact file (by sha1), if known.

These redirects are implemented by querying the same scholar elasticsearch
backend index, finding fulltext access with the matching type and URL/path
substring, and redirecting.


### Design Notes

This particular access URL format came from extensive discussion with large
indexing operators. Some of the properties are:

- links are to `scholar.archive.org`, the same domain as the landing page, even though the content is actually served (via redirect) from archive.org or web.archive.org
- lookups (by work ident) are fast against scholar.archive.org elasticsearch
- wayback "original URLs" are preserved in the URL itself
- would be feasible to do a static (nginx) redirect if project is ever wound-down
- wayback timestamps are not included in the URL, meaning that simple changes (recrawls) do not update the `citation_pdf_url` (this was a third-party concern)


# Sitemap

The sitemap setup will be copied from fatcat.wiki. The new resources (URLs)
will include:

    /robots.txt - updated to include sitemap references
    /sitemap.xml - basic generic list of pages (homepage, about, userguide)
    /sitemap-index-works.xml - XML file pointing to many sub-sitemap files; includes lastmod metadata
    /sitemap-index-access.xml - XML file pointing to many sub-sitemap files; includes lastmod metadata
    /sitemap-works-NNNNN.txt - series of "simple" sitemaps (URL list files), to landing pages
    /sitemap-access-NNNNN.txt - series of "simple" sitemaps (URL list files), to access links

Only works for which there is an appropriate fulltext access URL end up in the sitemaps.

The sitemap links from robots.txt should be absolute URLs, not relative URLs.
