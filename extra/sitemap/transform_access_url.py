#!/usr/bin/env python3

import sys

# NOTE: copied from fatcat_scholar/hacks.py
def make_access_redirect_url(access_type: str, access_url: str) -> str:
    if access_type == "wayback" and "://web.archive.org/" in access_url:
        segments = access_url.split("/")
        dt = segments[4]
        original_url = "/".join(segments[5:])
        return f"https://scholar.archive.org/access/wayback/{dt}/{original_url}"
    elif access_type == "ia_file" and "://archive.org/download/" in access_url:
        suffix = "/".join(access_url.split("/")[4:])
        return f"https://scholar.archive.org/access/ia_file/{suffix}"
    else:
        return access_url

def run() -> None:
    for line in sys.stdin:
        (access_type, access_url) = line.strip().split('\t')
        print(make_access_redirect_url(access_type, access_url))

if __name__ == "__main__":
    run()
