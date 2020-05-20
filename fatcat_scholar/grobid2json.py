#!/usr/bin/env python3

"""
NB: adapted to work as a library for PDF extraction. Will probably be
re-written eventually to be correct, complete, and robust; this is just a
first iteration.

This script tries to extract everything from a GROBID TEI XML fulltext dump:

- header metadata
- affiliations
- references (with context)
- abstract
- fulltext
- tables, figures, equations

A flag can be specified to disable copyright encumbered bits (--no-emcumbered):

- abstract
- fulltext
- tables, figures, equations

Prints JSON to stdout, errors to stderr

This file copied from the sandcrawler repository.
"""

import io
import json
import argparse
import xml.etree.ElementTree as ET

xml_ns = "http://www.w3.org/XML/1998/namespace"
ns = "http://www.tei-c.org/ns/1.0"

def all_authors(elem):
    names = []
    for author in elem.findall('.//{%s}author' % ns):
        pn = author.find('./{%s}persName' % ns)
        if not pn:
            continue
        given_name = pn.findtext('./{%s}forename' % ns) or None
        surname = pn.findtext('./{%s}surname' % ns) or None
        full_name = ' '.join(pn.itertext())
        obj = dict(name=full_name)
        if given_name:
            obj['given_name'] = given_name
        if surname:
            obj['surname'] = surname
        ae = author.find('./{%s}affiliation' % ns)
        if ae:
            affiliation = dict()
            for on in ae.findall('./{%s}orgName' % ns):
                affiliation[on.get('type')] = on.text
            addr_e = ae.find('./{%s}address' % ns)
            if addr_e:
                address = dict()
                for t in addr_e.getchildren():
                    address[t.tag.split('}')[-1]] = t.text
                if address:
                    affiliation['address'] = address
                #affiliation['address'] = {
                #    'post_code': addr.findtext('./{%s}postCode' % ns) or None,
                #    'settlement': addr.findtext('./{%s}settlement' % ns) or None,
                #    'country': addr.findtext('./{%s}country' % ns) or None,
                #}
            obj['affiliation'] = affiliation
        names.append(obj)
    return names


def journal_info(elem):
    journal = dict()
    journal['name'] = elem.findtext('.//{%s}monogr/{%s}title' % (ns, ns))
    journal['publisher'] = elem.findtext('.//{%s}publicationStmt/{%s}publisher' % (ns, ns))
    if journal['publisher'] == '':
        journal['publisher'] = None
    journal['issn'] = elem.findtext('.//{%s}idno[@type="ISSN"]' % ns)
    journal['eissn'] = elem.findtext('.//{%s}idno[@type="eISSN"]' % ns)
    journal['volume'] = elem.findtext('.//{%s}biblScope[@unit="volume"]' % ns)
    journal['issue'] = elem.findtext('.//{%s}biblScope[@unit="issue"]' % ns)
    keys = list(journal.keys())

    # remove empty/null keys
    for k in keys:
        if not journal[k]:
            journal.pop(k)
    return journal


def biblio_info(elem):
    ref = dict()
    ref['id'] = elem.attrib.get('{http://www.w3.org/XML/1998/namespace}id')
    # Title stuff is messy in references...
    ref['title'] = elem.findtext('.//{%s}analytic/{%s}title' % (ns, ns))
    other_title = elem.findtext('.//{%s}monogr/{%s}title' % (ns, ns))
    if other_title:
        if ref['title']:
            ref['journal'] = other_title
        else:
            ref['journal'] = None
            ref['title'] = other_title
    ref['authors'] = all_authors(elem)
    ref['publisher'] = elem.findtext('.//{%s}publicationStmt/{%s}publisher' % (ns, ns))
    if ref['publisher'] == '':
        ref['publisher'] = None
    date = elem.find('.//{%s}date[@type="published"]' % ns)
    ref['date'] = (date != None) and date.attrib.get('when')
    ref['volume'] = elem.findtext('.//{%s}biblScope[@unit="volume"]' % ns)
    ref['issue'] = elem.findtext('.//{%s}biblScope[@unit="issue"]' % ns)
    el = elem.find('.//{%s}ptr[@target]' % ns)
    if el is not None:
        ref['url'] = el.attrib['target']
        # Hand correction
        if ref['url'].endswith(".Lastaccessed"):
            ref['url'] = ref['url'].replace(".Lastaccessed", "")
    else:
        ref['url'] = None
    return ref


def teixml2json(content, encumbered=True):

    if type(content) == str:
        content = io.StringIO(content)
    elif type(content) == bytes:
        content = io.BytesIO(content)

    info = dict()

    #print(content)
    #print(content.getvalue())
    tree = ET.parse(content)
    tei = tree.getroot()

    header = tei.find('.//{%s}teiHeader' % ns)
    if header is None:
        raise ValueError("XML does not look like TEI format")
    application_tag = header.findall('.//{%s}appInfo/{%s}application' % (ns, ns))[0]
    info['grobid_version'] = application_tag.attrib['version'].strip()
    info['grobid_timestamp'] = application_tag.attrib['when'].strip()
    info['title'] = header.findtext('.//{%s}analytic/{%s}title' % (ns, ns))
    info['authors'] = all_authors(header.find('.//{%s}sourceDesc/{%s}biblStruct' % (ns, ns)))
    info['journal'] = journal_info(header)
    date = header.find('.//{%s}date[@type="published"]' % ns)
    info['date'] = (date != None) and date.attrib.get('when')
    info['fatcat_release'] = header.findtext('.//{%s}idno[@type="fatcat"]' % ns)
    info['doi'] = header.findtext('.//{%s}idno[@type="DOI"]' % ns)
    if info['doi']:
        info['doi'] = info['doi'].lower()

    refs = []
    for (i, bs) in enumerate(tei.findall('.//{%s}listBibl/{%s}biblStruct' % (ns, ns))):
        ref = biblio_info(bs)
        ref['index'] = i
        refs.append(ref)
    info['citations'] = refs

    text = tei.find('.//{%s}text' % (ns))
    #print(text.attrib)
    if text.attrib.get('{%s}lang' % xml_ns):
        info['language_code'] = text.attrib['{%s}lang' % xml_ns]  # xml:lang

    if encumbered:
        el = tei.find('.//{%s}profileDesc/{%s}abstract' % (ns, ns))
        info['abstract'] = (el or None) and " ".join(el.itertext()).strip()
        el = tei.find('.//{%s}text/{%s}body' % (ns, ns))
        info['body'] = (el or None) and " ".join(el.itertext()).strip()
        el = tei.find('.//{%s}back/{%s}div[@type="acknowledgement"]' % (ns, ns))
        info['acknowledgement'] = (el or None) and " ".join(el.itertext()).strip()
        el = tei.find('.//{%s}back/{%s}div[@type="annex"]' % (ns, ns))
        info['annex'] = (el or None) and " ".join(el.itertext()).strip()

    # remove empty/null keys
    keys = list(info.keys())
    for k in keys:
        if not info[k]:
            info.pop(k)
    return info

def main():   # pragma no cover
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="GROBID TEI XML to JSON",
        usage="%(prog)s [options] <teifile>...")
    parser.add_argument("--no-encumbered",
        action="store_true",
        help="don't include ambiguously copyright encumbered fields (eg, abstract, body)")
    parser.add_argument("teifiles", nargs='+')

    args = parser.parse_args()

    for filename in args.teifiles:
        content = open(filename, 'r')
        print(json.dumps(
            teixml2json(content,
               encumbered=(not args.no_encumbered)),
            sort_keys=True))

if __name__=='__main__':   # pragma no cover
    main()
