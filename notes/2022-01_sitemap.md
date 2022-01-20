
## 2022-01-20

Updated sitemap.xml, and now have 23.9M access URLs, which compares with 17.9M
previously (an additional 6 million URLs!).

Here is how various filters impact this number, based on queries in
scholar.archive.org right now:

    # default: papers or pages of microfilm, with any known IA fulltext preservation
    https://scholar.archive.org/search?q=*
    => 74,356,823

    # papers, with metadata records, with any IA fulltext preservation
    https://scholar.archive.org/search?q=doc_type%3Awork
    => 33,797,527

    # all documents (papers, reports, posts, etc), with metadata records, and any IA fulltext preservation
    https://scholar.archive.org/search?q=doc_type%3Awork&filter_type=everything
    => 35,256,465

    # same as above, plus direct public access (PDF or HTML but not microfilm)
    https://scholar.archive.org/search?q=doc_type%3Awork+%28fulltext.access_type%3Aia_file+OR+fulltext.access_type%3Awayback%29&filter_type=everything
    => 33,999,135

    # same as above, removing arxiv.org and Pubmed Central papers
    https://scholar.archive.org/search?q=doc_type%3Awork+%28fulltext.access_type%3Aia_file+OR+fulltext.access_type%3Awayback%29+%28NOT+biblio.arxiv_id%3A*%29+%28NOT+biblio.pmcid%3A*%29&filter_type=everything
    => 27,745,435

    # same as above, remove papers from large publishers which are not explicitly under open license
    https://scholar.archive.org/search?q=doc_type%3Awork+%28fulltext.access_type%3Aia_file+OR+fulltext.access_type%3Awayback%29+%28NOT+biblio.arxiv_id%3A*%29+%28NOT+biblio.pmcid%3A*%29+%28%28NOT+biblio.publisher_type%3Abig5%29+OR+year%3A%3C1926+OR+tags%3Aoa%29&filter_type=everything
    => 24,200,138

In a post-processing step (which can not be expressed as a query), we are also
removing about 300k "green OA" URLs. These are a subset of the cases where a
pre-print is available but published version is not. I will plan on removing
this in the next iteration of the sitemap.
