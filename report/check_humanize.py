"""Stage 4 check: humanized prose must keep every number, citation key, cross-reference and structural line."""
import re, sys
from collections import Counter
from pathlib import Path
H = Path(__file__).resolve().parent
NUM = re.compile(r"(?<![\w.])[−-]?\d+(?:\.\d+)?")
ok = True
for f in sorted((H / "content_verified").glob("0[0-8]*.md")):
    a, b = f.read_text(), (H / "content" / f.name).read_text()
    for name, pat in (("numbers", NUM), ("citations", re.compile(r"@\w+(?=[;\]])")), ("xrefs", re.compile(r"@(?:fig|tab|eq):\w+")),
                      ("struct", re.compile(r"^(?:FIG|TAB|EQ|#|\|).*$", re.M))):
        ca, cb = Counter(pat.findall(a)), Counter(pat.findall(b))
        if ca != cb:
            ok = False
            print(f"{f.name} {name}: removed {dict(ca - cb)} added {dict(cb - ca)}")
    wa, wb = len(a.split()), len(b.split())
    print(f"{f.name}: words {wa} -> {wb}")
print("OK: numbers, citations, cross-references and structure unchanged" if ok else "DIFFERENCES FOUND")
sys.exit(0 if ok else 1)
