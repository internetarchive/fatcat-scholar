

Thinking of simple ways to reduce query parse errors and handle more queries as
expected. In particular:

- handle slashes in query tokens (eg, "N/A" without quotes)
- handle semi-colons in queries, when they are not intended as filters
- if query "looks like" a raw citation string, detect that and do citation
  parsing in to a structured format, then do a query or fuzzy lookup from there


## Questions/Thoughts

Should we detect title lookups in addition to full citation lookups? Probably
too complicated.

Do we have a static list of colon-prefixes, or load from the schema mapping
file itself?
