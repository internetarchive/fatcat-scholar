from typing import Optional

DOI_PREFIX_MAP = {
    # simple entries (mostly OA and platforms)
    "10.2307": {"domain": "jstor.org"},
    "10.11501": {"domain": "ndl.go.jp"},
    "10.6084": {"domain": "figshare.com"},
    "10.5281": {"domain": "zenodo.org"},
    "10.1590": {"domain": "scielo.br"},
    "10.1371": {"domain": "plos.org"},
    "10.1155": {"domain": "hindawi.com"},
    "10.7554": {"domain": "elifesciences.com"},
    "10.1145": {"domain": "acm.org"},
    # more complex publisher mappings (verify journal/publisher)
    "10.1016": {"domain": "elsevier.com", "publisher": "elsevier"},
    "10.1007": {"domain": "springer.com", "publisher": "springer"},
    "10.1186": {"domain": "springer.com", "publisher": "springer"},
    "10.1002": {"domain": "wiley.com", "publisher": "wiley"},
    "10.1109": {"domain": "ieee.com", "publisher": "ieee"},
    "10.1080": {"domain": "tandfonline.com", "publisher": "informa"},
    "10.1093": {"domain": "oup.com", "publisher": "oxford"},
    "10.1111": {"domain": "sagepub.com", "publisher": "sage"},
    "10.1042": {"domain": "sagepub.com", "publisher": "sage"},
    "10.1177": {"domain": "sagepub.com", "publisher": "sage"},
    "10.1021": {"domain": "acs.org", "publisher": "acs"},
    "10.1017": {"domain": "cambridge.org", "publisher": "cambridge"},
    # "10.1097": {"domain": "lww.org",    "publisher": "wolters"},
    "10.1515": {"domain": "degruyter.com", "publisher": "gruyter"},
    "10.1038": {"domain": "nature.com", "container_name": "nature"},
    "10.1163": {"domain": "brill.com", "publisher": "brill"},
    "10.3390": {"domain": "mdpi.com", "publisher": "mdpi"},
    "10.1128": {"domain": "asm.org", "publisher": "microbiology"},
    "10.1103": {"domain": "aps.org", "publisher": "physical"},
    "10.3389": {"domain": "frontiersin.org", "publisher": "frontiers"},
    "10.1136": {"domain": "bmj.org", "publisher": "bmj"},
    "10.1088": {"domain": "iop.org", "publisher": "iop"},
    "10.1086": {"domain": "iop.org", "publisher": "iop"},
    "10.1142": {"domain": "worldscientific.com", "publisher": "world"},
    "10.1126": {"domain": "sciencemag.org", "container_name": "science"},
    "10.1162": {"domain": "mitpressjournals.org", "publisher": "mit"},
    "10.1045": {"domain": "dlib.org", "container_name": "d-lib"},
    "10.17723": {"domain": "archivists.org", "publisher": "archiv"},
    "10.2139": {"domain": "ssrn.com", "container_name": "social science"},
}


def doi_link_domain(
    doi_prefix: str, container_name: Optional[str], publisher: Optional[str]
) -> Optional[str]:
    """
    Takes a DOI prefix and a publisher name, and tries to guess which domain
    name the DOI will resolve to. This is used for display only.

    helpful: https://gist.github.com/TomDemeranville/8699224

    TODO: JSTOR, biorxiv, medrxiv, zenodo, figshare, dryad, etc
    """

    # manual cases first
    if doi_prefix == "10.1101" and container_name:
        if "biorxiv" in container_name.lower():
            return "biorxiv.org"
        elif "medrxiv" in container_name.lower():
            return "medrxiv.org"
        else:
            return None
    elif doi_prefix == "10.1101" and container_name:
        if "lancet" in container_name.lower():
            return "thelancet.com"

    # then the map
    meta = DOI_PREFIX_MAP.get(doi_prefix)
    if not meta:
        return None

    if meta.get("publisher"):
        if not publisher or meta["publisher"] not in publisher.lower():
            return None
    if meta.get("container_name"):
        if not container_name or meta["container_name"] not in container_name.lower():
            return None
    return meta.get("domain")
