
## High-Level

Work-oriented: base input is arrays of expanded releases, all from the same
work.

Re-index pipeline would look at fatcat changelog or existing release feed, and
use the `work_id` to fetch all other releases.

Batch indexing pipeline would use a new variant of `fatcat-export` which is
expanded releases (one-per-line), grouped (or sorted) by work id.

Then, pipeline looks like:

- choose canonical release
- choose best access
- choose best fulltext file
    => iterate releases and files
    => soft prefer canonical release, file access, release_date, etc
    => check via postgrest query that fulltext is available
    => fetch raw fulltext
- check if we expect a SIM copy to exist
    => eg, using an issue db?
    => if so, fetch petabox metadata and try to confirm, so we can create a URL
    => if we don't have another fulltext source (?):
        => fetch djvu file and extract the pages in question (or just 1 if unsure?)
- output "heavy" object

Next step is:

- summarize biblio metadata
- select one abstract per language
- sanitize abstracts and fulltext content for indexing
- compute counts, epistimological quality, etc

The output of that goes to Kafka for indexing into ES.

This indexing process is probably going to be both CPU and network intensive.
In python will want multiprocessing and maybe also async?

## Implementation

Existing tools/libraries:

- fatcat-openapi-client
- postgrest client
- S3/minio/seaweed client
- ftfy
- language detection

New needed (eventually):

- strip latex
- strip JATS or HTML
