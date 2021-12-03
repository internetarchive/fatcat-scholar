
CREATE TABLE IF NOT EXISTS sim_pub (
    sim_pubid TEXT NOT NULL PRIMARY KEY,
    pub_collection TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    issn TEXT,
    pub_type TEXT,
    publisher TEXT,
    container_issnl TEXT,
    container_ident TEXT,
    wikidata_qid TEXT
);

CREATE TABLE IF NOT EXISTS sim_issue (
    issue_item TEXT NOT NULL PRIMARY KEY,
    sim_pubid NOT NULL,
    year INTEGER,
    volume TEXT,
    issue TEXT,
    first_page INTEGER,
    last_page INTEGER,
    release_count INTEGER,
    FOREIGN KEY(sim_pubid) REFERENCES sim_pub(sim_pubid)
);

-- intent here is to capture how many releases are just not getting matched due
-- to missing issue metadata
CREATE TABLE IF NOT EXISTS release_counts (
    sim_pubid TEXT NOT NULL,
    year TEXT NOT NULL,
    volume TEXT NOT NULL,
    release_count INTEGER NOT NULL,
    PRIMARY KEY(sim_pubid, year, volume),
    FOREIGN KEY(sim_pubid) REFERENCES sim_pub(sim_pubid)
);
