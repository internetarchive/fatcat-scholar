
from io import StringIO
from typing import List, Dict, Tuple, Optional, Any, Sequence
import xml.etree.ElementTree as ET

def djvu_extract_leaf_texts(blob: StringIO, only_leaves: Optional[List[int]] = None) -> Dict[int, str]:
    """
    Takes an in-memory djvu XML string (note: not an actual djvu file, just the
    IA XML file type), and iterates throug
    """

    leaf_text = dict()
    max_leaf = None
    if only_leaves:
        max_leaf = max(only_leaves)
    elem_iter = ET.iterparse(blob, ["start", "end"])
    for (event, element) in elem_iter:
        if event == "start":
            continue
        if not (element.tag == "OBJECT" and event == "end"):
            continue

        # <OBJECT data="file://localhost//tmp/derive/ERIC_ED441501//ERIC_ED441501.djvu" height="6545" type="image/x.djvu" usemap="ERIC_ED441501_0002.djvu" width="5048">
        usemap = element.get('usemap')
        if not usemap:
            continue
        leaf_num = None
        try:
            leaf_num = int(usemap.replace('.djvu', '').split('_')[-1])
        except:
            continue
        if only_leaves is not None and leaf_num is not None:
            if leaf_num not in only_leaves:
                continue
            if max_leaf is not None and leaf_num > max_leaf:
                break
        paragraph_texts = []
        for paragraph in element.iter("PARAGRAPH"):
            tokens = [r.strip() for r in paragraph.itertext()]
            tokens = [t for t in tokens if t]
            p_text = " ".join(tokens)
            if p_text:
                paragraph_texts.append(p_text)
        page_text = "\n".join(paragraph_texts)
        #print(f"### {leaf_num}\n{page_text}\n")
        if page_text:
            leaf_text[leaf_num] = page_text
        element.clear()
    return leaf_text
