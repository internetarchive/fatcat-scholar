#!/usr/bin/env python3

import glob
import datetime

def index_entity(entity_type, output) -> None:

    now = datetime.date.today().isoformat()
    print("""<?xml version="1.0" encoding="UTF-8"?>""", file=output)
    print("""<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">""", file=output)

    for filename in glob.glob(f"sitemap-{entity_type}-*.txt"):
        print("  <sitemap>", file=output)
        print(f"    <loc>https://scholar.archive.org/{filename}</loc>", file=output)
        print(f"    <lastmod>{now}</lastmod>", file=output)
        print("  </sitemap>", file=output)

    print("</sitemapindex>", file=output)

def main() -> None:
    with open('sitemap-index-works.xml', 'w') as output:
        index_entity("works", output)
    with open('sitemap-index-access.xml', 'w') as output:
        index_entity("access", output)

if __name__=="__main__":
    main()
