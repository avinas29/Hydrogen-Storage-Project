"""Build the B.Tech report DOCX inside the official template.

    .venv/bin/python -m report.build_report            # two passes: build, render, read page numbers, rebuild

Content: report/content/*.md (light markup, see parse()). References: report/refs.py.
Template: report/template/BTP_Report_Format_Word.docx (title page, certificate, styles, footer kept).
Outputs: report/output/BTP_Report.docx, .pdf, and report/output/build_log.json.
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Twips
from PIL import Image

from .refs import REFS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
TEMPLATE = HERE / "template/BTP_Report_Format_Word.docx"
CONTENT = HERE / "content"
OUTDIR = HERE / "output"
TITLE = ("Machine Learning-Assisted Discovery and Application-Specific Screening of Metal Hydride Materials "
         "for Hydrogen Storage")
STUDENT, ROLL, GUIDE = "Avinash", "230151005", "Dr. Saket Verma"
DESIGNATION = "Assistant Professor"
TEXT_W_TW = 12240 - 1531 - 1304          # text width in twips (template margins)
TOC_TAB = 8787                            # template's page-number tab stop
APPX = "ABCDEFGH"


# ----------------------------------------------------------------------------------------------- parsing
@dataclass
class Block:
    kind: str                 # para, bullet, num, fig, tab, eq, sec, note
    text: str = ""
    key: str = ""
    path: str = ""
    width: float = 15.0
    rows: list = field(default_factory=list)
    label: str = ""


@dataclass
class Chapter:
    label: str                # "1" or "A"
    title: str
    appendix: bool
    blocks: list = field(default_factory=list)


def parse_chapters() -> list[Chapter]:
    chapters: list[Chapter] = []
    files = sorted(p for p in CONTENT.glob("*.md") if not p.name.startswith("00_"))
    n_ch = n_ap = 0
    for f in files:
        lines = f.read_text().splitlines()
        i = 0
        para: list[str] = []

        def flush():
            if para:
                t = " ".join(s.strip() for s in para)
                chapters[-1].blocks.append(Block("note" if t.startswith(("†", "‡", "§")) else "para", t))
                para.clear()

        while i < len(lines):
            ln = lines[i]
            if ln.startswith("#A "):
                flush(); chapters.append(Chapter(APPX[n_ap], ln[3:].strip(), True)); n_ap += 1
            elif ln.startswith("# "):
                flush(); n_ch += 1; chapters.append(Chapter(str(n_ch), ln[2:].strip(), False))
            elif ln.startswith("## "):
                flush(); chapters[-1].blocks.append(Block("sec", ln[3:].strip()))
            elif ln.startswith("FIG "):
                flush()
                key, path, width, cap = [s.strip() for s in ln[4:].split("|", 3)]
                chapters[-1].blocks.append(Block("fig", cap, key, path, float(width)))
            elif ln.startswith("EQ "):
                flush()
                key, eq = [s.strip() for s in ln[3:].split("|", 1)]
                chapters[-1].blocks.append(Block("eq", eq, key))
            elif ln.startswith("TAB "):
                flush()
                key, cap = [s.strip() for s in ln[4:].split("|", 1)]
                rows = []
                i += 1
                while i < len(lines) and lines[i].startswith("|"):
                    if not re.match(r"^\|[\s\-|:]+\|\s*$", lines[i]):
                        rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                    i += 1
                chapters[-1].blocks.append(Block("tab", cap, key, rows=rows))
                continue
            elif ln.startswith("- "):
                flush(); chapters[-1].blocks.append(Block("bullet", ln[2:].strip()))
            elif re.match(r"^\d+\. ", ln):
                flush(); n, t = ln.split(" ", 1); chapters[-1].blocks.append(Block("num", t.strip(), label=n))
            elif not ln.strip():
                flush()
            else:
                para.append(ln)
            i += 1
        flush()
    return chapters


def parse_front() -> dict[str, str]:
    txt = (CONTENT / "00_front.md").read_text()
    parts = re.split(r"^@@(\w+)\s*$", txt, flags=re.M)
    return {parts[k]: parts[k + 1].strip() for k in range(1, len(parts), 2)}


# ----------------------------------------------------------------------------------------------- numbering
CITE = re.compile(r"\[(@\w+(?:\s*;\s*@\w+)*)\]")
XREF = re.compile(r"@(fig|tab|eq):(\w+)")


def number(chapters: list[Chapter], front: dict) -> tuple[dict, dict, list]:
    labels: dict[str, str] = {}
    toc: list[tuple] = []
    for ch in chapters:
        s = f = t = e = 0
        toc.append(("chap", ch))
        for b in ch.blocks:
            if b.kind == "sec":
                s += 1; b.label = f"{ch.label}.{s}"; toc.append(("sec", b))
            elif b.kind == "fig":
                f += 1; b.label = f"{ch.label}.{f}"; labels["fig:" + b.key] = b.label
            elif b.kind == "tab":
                t += 1; b.label = f"{ch.label}.{t}"; labels["tab:" + b.key] = b.label
            elif b.kind == "eq":
                e += 1; b.label = f"{ch.label}.{e}"; labels["eq:" + b.key] = b.label
    order: dict[str, int] = {}
    texts = [b.text for ch in chapters for b in ch.blocks] + \
            [c for ch in chapters for b in ch.blocks if b.kind == "tab" for r in b.rows for c in r]
    for tx in texts:
        for m in CITE.finditer(tx):
            for k in re.findall(r"@(\w+)", m.group(1)):
                if k not in REFS:
                    raise KeyError(f"unknown reference key {k}")
                order.setdefault(k, len(order) + 1)
    return labels, order, toc


def cite_text(keys: list[str], order: dict) -> str:
    nums = sorted(order[k] for k in keys)
    out, run = [], [nums[0]]
    for n in nums[1:]:
        if n == run[-1] + 1:
            run.append(n)
        else:
            out.append(run); run = [n]
    out.append(run)
    return "[" + ", ".join(f"{r[0]}–{r[-1]}" if len(r) > 2 else ", ".join(map(str, r)) for r in out) + "]"


def resolve(text: str, labels: dict, order: dict) -> str:
    text = CITE.sub(lambda m: cite_text(re.findall(r"@(\w+)", m.group(1)), order), text)

    def x(m):
        k = f"{m.group(1)}:{m.group(2)}"
        if k not in labels:
            raise KeyError(f"unresolved cross-reference {k}")
        return {"fig": "Fig. ", "tab": "Table ", "eq": "Eq. ("}[m.group(1)] + labels[k] + (")" if m.group(1) == "eq" else "")
    return XREF.sub(x, text)


# ----------------------------------------------------------------------------------------------- docx helpers
TOKEN = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|~[^~]+?~|\^[^^]+?\^|`[^`]+?`)")


SUB = str.maketrans("₀₁₂₃₄₅₆₇₈₉ₓ₋.", "0123456789x−.")
SUP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789−")


def unicode_scripts(text: str) -> str:
    """Unicode sub/superscript characters -> ~sub~ / ^sup^ markup, so they render as real TNR sub/superscripts."""
    text = re.sub(r"[₀-₉ₓ₋](?:[₀-₉ₓ₋.]*[₀-₉ₓ])?", lambda m: "~" + m.group(0).translate(SUB) + "~", text)
    return re.sub(r"[⁰-⁹⁻¹²³]+", lambda m: "^" + m.group(0).translate(SUP) + "^", text)


def add_runs(p, text: str, size: float | None = None, bold: bool = False, italic: bool = False, color=None):
    text = unicode_scripts(text)
    for part in TOKEN.split(text):
        if not part:
            continue
        b, it, sub, sup, code = bold, italic, False, False, False
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            part, b = part[2:-2], True
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            part, it = part[1:-1], True
        elif part.startswith("~") and part.endswith("~"):
            part, sub = part[1:-1], True
        elif part.startswith("^") and part.endswith("^"):
            part, sup = part[1:-1], True
        elif part.startswith("`") and part.endswith("`"):
            part, code = part[1:-1], True
        # nested emphasis inside bold (e.g. **... *x* ...**) is rare: render inner text plainly
        r = p.add_run(part)
        r.bold, r.italic = b or None, it or None
        if sub:
            r.font.subscript = True
        if sup:
            r.font.superscript = True
        if code:
            r.font.name = "Courier New"
            r.font.size = Pt((size or 12) - 1.5)
        elif size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = color
    return p


def set_spacing(p, before=None, after=None, line=None):
    pf = p.paragraph_format
    if before is not None:
        pf.space_before = Pt(before)
    if after is not None:
        pf.space_after = Pt(after)
    if line is not None:
        pf.line_spacing = line


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def heading_prelim(doc, text, toc_level=None):
    """Preliminary-page heading in the template's look (centred, 16 pt bold, 30 pt after), on a new page."""
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = True
    set_spacing(p, after=30)
    r = p.add_run(text); r.bold = True; r.font.size = Pt(16)
    return p


def chapter_heading(doc, label: str, title: str, appendix: bool):
    """'Chapter N' (14 pt) and the title (18 pt) as one Heading 1 paragraph, so it carries an outline level."""
    p = doc.add_paragraph(style="Heading 1")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = True
    set_spacing(p, before=0, after=25)
    r = p.add_run(("Appendix " if appendix else "Chapter ") + label)
    style_run(r, 14)
    r.add_break()
    r2 = p.add_run(title)
    style_run(r2, 18)
    return p


def style_run(r, size):
    r.bold = True
    r.font.size = Pt(size)
    r.font.name = "Times New Roman"
    r.font.color.rgb = RGBColor(0, 0, 0)
    rpr = r._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    for a in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
        if fonts is not None and fonts.get(qn(a)) is not None:
            del fonts.attrib[qn(a)]
    fonts.set(qn("w:ascii"), "Times New Roman"); fonts.set(qn("w:hAnsi"), "Times New Roman")


def body_para(doc, text, labels, order, size=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY, style=None):
    p = doc.add_paragraph(style=style) if style else doc.add_paragraph()
    p.alignment = align
    add_runs(p, resolve(text, labels, order), size=size)
    return p


def caption(doc, kind: str, label: str, text: str, labels, order, style_name: str):
    p = doc.add_paragraph(style=style_name)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER if kind == "Figure" else WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(f"{kind} {label}: ")
    r.bold = True
    add_runs(p, resolve(text, labels, order))
    if kind == "Table":
        p.paragraph_format.keep_with_next = True
        set_spacing(p, before=6, after=3)
    else:
        set_spacing(p, before=3, after=10)
    return p


def ensure_caption_styles(doc):
    from docx.enum.style import WD_STYLE_TYPE
    for name in ("Figure Caption", "Table Caption"):
        if name not in [s.name for s in doc.styles]:
            st = doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
            st.base_style = doc.styles["Caption"]
            st.quick_style = True


TBLPR_ORDER = ["tblStyle", "tblpPr", "tblOverlap", "bidiVisual", "tblStyleRowBandSize", "tblStyleColBandSize", "tblW", "jc",
               "tblCellSpacing", "tblInd", "tblBorders", "shd", "tblLayout", "tblCellMar", "tblLook", "tblCaption",
               "tblDescription"]
TCPR_ORDER = ["cnfStyle", "tcW", "gridSpan", "hMerge", "vMerge", "tcBorders", "shd", "noWrap", "tcMar", "textDirection",
              "tcFitText", "vAlign", "hideMark"]


def insert_ordered(parent, el, order):
    tag = el.tag.split("}")[1]
    for old in parent.findall(el.tag):
        parent.remove(old)
    later = order[order.index(tag) + 1:]
    for child in parent.iterchildren():
        if child.tag.split("}")[1] in later:
            child.addprevious(el)
            return el
    parent.append(el)
    return el


def set_cell_border(cell, **edges):
    tcPr = cell._element.get_or_add_tcPr()
    b = tcPr.find(qn("w:tcBorders"))
    if b is None:
        b = insert_ordered(tcPr, OxmlElement("w:tcBorders"), TCPR_ORDER)
    for edge, (sz, color) in edges.items():
        el = OxmlElement(f"w:{edge}")
        el.set(qn("w:val"), "single"); el.set(qn("w:sz"), str(sz)); el.set(qn("w:color"), color)
        b.append(el)


def shade(cell, fill):
    tcPr = cell._element.get_or_add_tcPr()
    s = OxmlElement("w:shd"); s.set(qn("w:val"), "clear"); s.set(qn("w:color"), "auto"); s.set(qn("w:fill"), fill)
    insert_ordered(tcPr, s, TCPR_ORDER)


def col_widths(rows, total=TEXT_W_TW, font=9.5):
    """Proportional to content, but never narrower than the longest single word (no broken words)."""
    n = len(rows[0])
    cw = 0.50 * font * 20                      # approx. average character width in twips
    clean = lambda s: re.sub(r"[~^*`]", "", s)  # noqa: E731
    minw, want = [], []
    for j in range(n):
        cells = [clean(r[j]) for r in rows]
        word = max([len(w) for c in cells[1:] for w in c.split()] + [len(w) * 1.15 for w in cells[0].split()] + [1])
        minw.append(int(word * cw * 1.1 + 230))
        vals = [len(c) for c in cells]
        want.append(max(word, min(max(vals), 42)) * 0.7 + 0.3 * sum(vals) / len(vals))
    free = total - sum(minw)
    if free <= 0:
        k = total / sum(minw)
        return [int(m * k) for m in minw]
    extra = [max(0.0, w * cw - m) for w, m in zip(want, minw)]
    tot = sum(extra) or 1
    return [int(m + free * e / tot) for m, e in zip(minw, extra)]


def add_table(doc, rows, labels, order, font=9):
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    t = doc.add_table(rows=len(rows), cols=n)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    widths = col_widths(rows, font=font)
    tblPr = t._element.tblPr
    lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); insert_ordered(tblPr, lay, TBLPR_ORDER)
    tw = OxmlElement("w:tblW"); tw.set(qn("w:w"), str(sum(widths))); tw.set(qn("w:type"), "dxa")
    insert_ordered(tblPr, tw, TBLPR_ORDER)
    grid = t._element.find(qn("w:tblGrid"))
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths):
        gc.set(qn("w:w"), str(w))
    for i, r in enumerate(rows):
        tr = t.rows[i]
        trPr = tr._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit"); trPr.append(cs)
        if i == 0:
            th = OxmlElement("w:tblHeader"); trPr.append(th)
        for j, txt in enumerate(r):
            c = tr.cells[j]
            c.width = Twips(widths[j])
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            set_spacing(p, before=1, after=1, line=1.0)
            add_runs(p, resolve(txt, labels, order), size=font, bold=(i == 0))
            edges = {}
            if i == 0:
                edges["top"] = (8, "000000"); edges["bottom"] = (6, "000000"); shade(c, "E7EEF6")
            if i == len(rows) - 1:
                edges["bottom"] = (8, "000000")
            elif i > 0:
                edges["bottom"] = (2, "BFBFBF")
            set_cell_border(c, **edges)
    # keep rows together with the caption where possible
    for row in t.rows[:-1]:
        for c in row.cells:
            c.paragraphs[0].paragraph_format.keep_with_next = True
    return t


def add_equation(doc, eq, label, labels, order):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.tab_stops.add_tab_stop(Twips(TEXT_W_TW // 2), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Twips(TEXT_W_TW), WD_TAB_ALIGNMENT.RIGHT)
    set_spacing(p, before=4, after=8)
    p.add_run("\t")
    add_runs(p, resolve(eq, labels, order), italic=False)
    p.add_run(f"\t({label})")
    return p


def add_figure(doc, path, width_cm):
    img = ROOT / path
    w, h = Image.open(img).size
    max_h = 9.2
    width = min(width_cm, 16.4, max_h * w / h)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    set_spacing(p, before=6, after=0)
    p.add_run().add_picture(str(img), width=Cm(width))


def field_para(doc, instr: str, entries: list[tuple[int, str, str, bool]]):
    """A TOC field whose cached result is our static entries [(indent_level, text, page, bold)]."""
    def fld(p, typ):
        r = p.add_run(); fc = OxmlElement("w:fldChar"); fc.set(qn("w:fldCharType"), typ); r._element.append(fc)

    first = True
    paras = []
    for lvl, text, page, bold in entries:
        p = doc.add_paragraph()
        pf = p.paragraph_format
        pf.tab_stops.add_tab_stop(Twips(TOC_TAB), WD_TAB_ALIGNMENT.LEFT)
        set_spacing(p, before=4 if (bold and lvl == 0 and text[:1].isdigit()) else 0, after=1.5, line=1.0)
        if lvl:
            pf.left_indent = Twips(369 * lvl)
        elif re.match(r"^[0-9A-H]+\.\d+  ", text):
            pf.left_indent = Twips(567); pf.first_line_indent = Twips(-567)
        if first:
            fld(p, "begin")
            r = p.add_run(); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = f" {instr} "
            r._element.append(it)
            fld(p, "separate")
            first = False
        add_runs(p, text, bold=bold, size=11)
        r = p.add_run("\t" + page)
        r.font.size = Pt(11)
        if bold:
            r.bold = True
        paras.append(p)
    if paras:
        fld(paras[-1], "end")
    else:
        p = doc.add_paragraph(); fld(p, "begin"); fld(p, "end")


SECT_ORDER = ["footnotePr", "endnotePr", "type", "pgSz", "pgMar", "paperSrc", "pgBorders", "lnNumType", "pgNumType",
              "cols", "formProt", "vAlign", "noEndnote", "titlePg", "textDirection", "bidi", "rtlGutter", "docGrid"]


def sect_insert(sectPr, tag: str, **attrs):
    """Insert a sectPr child in schema order (replacing an existing one)."""
    for old in sectPr.findall(qn(f"w:{tag}")):
        sectPr.remove(old)
    el = OxmlElement(f"w:{tag}")
    for k, v in attrs.items():
        el.set(qn(f"w:{k}"), v)
    later = SECT_ORDER[SECT_ORDER.index(tag) + 1:]
    for child in sectPr.iterchildren():
        if child.tag.split("}")[1] in later:
            child.addprevious(el)
            return el
    sectPr.append(el)
    return el


def roman(n: int) -> str:
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    out = ""
    for v, s in vals:
        while n >= v:
            out += s; n -= v
    return out


# ----------------------------------------------------------------------------------------------- build
def strip_markup(s: str) -> str:
    return re.sub(r"[*~^`]", "", s)


POSITIONAL = r"(?:a|b|left|right|centre|center|top|bottom|grey|orange|blue|red|bold|faint|light blue|dark blue)"


def short_caption(s: str) -> str:
    """List-of-figures/tables entry: first sentence, without positional/colour asides and a trailing parenthetical."""
    s = strip_markup(s).split(". ")[0].rstrip(".")
    s = re.sub(rf"\s*\({POSITIONAL}\b[^()]*\)", "", s)
    s = re.sub(r"\s*\([^()]*\)$", "", s).strip()
    return s


def build(pages: dict | None = None) -> tuple[Path, dict]:
    pages = pages or {}
    pg = lambda key: pages.get(key, "00")  # noqa: E731
    front = parse_front()
    chapters = parse_chapters()
    labels, order, toc = number(chapters, front)

    doc = Document(str(TEMPLATE))
    body = doc.element.body
    els = list(body.iterchildren())
    sect_final = els[-1]
    # keep title page (0-15) and certificate (16-24); drop the rest of the template's sample content
    for el in els[25:-1]:
        body.remove(el)
    P = doc.paragraphs
    P[0].runs[0].text = TITLE
    P[6].runs[0].text = STUDENT
    P[7].runs[0].text = f"({ROLL})"
    P[9].runs[0].text = GUIDE
    cert = P[17].runs
    cert[1].text = TITLE
    cert[2].text = f"” is a bona fide work of {STUDENT} ("
    cert[3].text = ROLL
    cert[4].text = "), carried out in the "
    full = "".join(r.text for r in P[22].runs)
    for r in P[22].runs[1:]:
        r.text = ""
    P[22].runs[0].text = full.replace("Your guide name", GUIDE)
    P[23].runs[0].text = f"{DESIGNATION},"
    ensure_caption_styles(doc)

    # ---------------- preliminary pages
    heading_prelim(doc, "Acknowledgements")
    for para in front["ACK"].split("\n\n"):
        lines = para.splitlines()
        if lines[0].strip() == STUDENT:
            for ln in lines:
                q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.RIGHT; add_runs(q, ln); set_spacing(q, after=0)
        else:
            body_para(doc, " ".join(lines), labels, order)
    heading_prelim(doc, "Abstract")
    for para in front["ABSTRACT"].split("\n\n"):
        body_para(doc, " ".join(para.splitlines()), labels, order)

    heading_prelim(doc, "Contents")
    entries = [(0, "List of Figures", pg("lof"), True), (0, "List of Tables", pg("lot"), True),
               (0, "List of Abbreviations and Symbols", pg("abbr"), True)]
    for kind, obj in toc:
        if kind == "chap":
            if obj.appendix and obj.label == "A":
                entries.append((0, "References", pg("refs"), True))
            name = f"{'Appendix ' if obj.appendix else ''}{obj.label}  {obj.title}"
            entries.append((0, name, pg(f"chap:{obj.label}"), True))
        else:
            entries.append((1, f"{obj.label}  {strip_markup(obj.text)}", pg(f"sec:{obj.label}"), False))
    if not any(c.appendix for c in chapters):
        entries.append((0, "References", pg("refs"), True))
    field_para(doc, 'TOC \\o "1-2" \\h \\z \\u', entries)

    heading_prelim(doc, "List of Figures")
    figs = [(c, b) for c in chapters for b in c.blocks if b.kind == "fig"]
    field_para(doc, 'TOC \\h \\z \\t "Figure Caption,1"',
               [(0, f"{b.label}  {short_caption(resolve(b.text, labels, order))}",
                 pg(f"fig:{b.label}"), False) for c, b in figs])
    heading_prelim(doc, "List of Tables")
    tabs = [(c, b) for c in chapters for b in c.blocks if b.kind == "tab"]
    field_para(doc, 'TOC \\h \\z \\t "Table Caption,1"',
               [(0, f"{b.label}  {short_caption(resolve(b.text, labels, order))}", pg(f"tab:{b.label}"), False)
                for c, b in tabs])
    heading_prelim(doc, "List of Abbreviations and Symbols")
    for k, tb in enumerate(re.findall(r"((?:^\|.*\|[ \t]*\n?)+)", front["ABBR"], re.M)):
        rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in tb.strip().splitlines()
                if not re.match(r"^\|[\s\-|:]+\|\s*$", l)]
        if k:
            doc.add_paragraph()
        add_table(doc, rows, labels, order, font=10)

    # section break: preliminary pages (roman) -> main matter (arabic from 1)
    new_sec = doc.add_section(WD_SECTION.NEW_PAGE)
    prelim_sectPr = doc.sections[-2]._sectPr
    sect_insert(prelim_sectPr, "pgNumType", fmt="lowerRoman", start="1")
    sect_insert(prelim_sectPr, "titlePg")            # title page without a number
    sect_insert(new_sec._sectPr, "pgNumType", fmt="decimal", start="1")
    first_footer = doc.sections[-2].first_page_footer
    first_footer.is_linked_to_previous = False
    for p in first_footer.paragraphs:
        p.text = ""

    # ---------------- chapters
    for ch in chapters:
        if ch.appendix and ch.label == "A":
            add_references(doc, order)
        h = chapter_heading(doc, ch.label, ch.title, ch.appendix)
        h.paragraph_format.page_break_before = not (ch.label == "1" and not ch.appendix)
        for b in ch.blocks:
            if b.kind == "sec":
                p = doc.add_paragraph(style="Heading 2")
                add_runs(p, f"{b.label}  {b.text}")
                set_spacing(p, before=12, after=4)
            elif b.kind == "para":
                body_para(doc, b.text, labels, order)
            elif b.kind == "note":
                q = body_para(doc, b.text, labels, order, size=9, align=WD_ALIGN_PARAGRAPH.LEFT); set_spacing(q, before=2)
            elif b.kind == "bullet":
                q = body_para(doc, b.text, labels, order, style="List Bullet"); set_spacing(q, after=3)
            elif b.kind == "num":
                q = doc.add_paragraph(); q.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                q.paragraph_format.left_indent = Twips(425); q.paragraph_format.first_line_indent = Twips(-425)
                q.paragraph_format.tab_stops.add_tab_stop(Twips(425))
                q.add_run(f"{b.label}\t")
                add_runs(q, resolve(b.text, labels, order))
                set_spacing(q, after=4)
            elif b.kind == "eq":
                add_equation(doc, b.text, b.label, labels, order)
            elif b.kind == "fig":
                add_figure(doc, b.path, b.width)
                caption(doc, "Figure", b.label, b.text, labels, order, "Figure Caption")
            elif b.kind == "tab":
                caption(doc, "Table", b.label, b.text, labels, order, "Table Caption")
                add_table(doc, b.rows, labels, order)
                sp = doc.add_paragraph(); set_spacing(sp, after=2)
    if not any(c.appendix for c in chapters):
        add_references(doc, order)

    # the template's final sectPr stays last; python-docx add_section put ours before it
    OUTDIR.mkdir(exist_ok=True)
    out = OUTDIR / "BTP_Report.docx"
    doc.save(out)
    meta = {"labels": labels, "cite_order": order,
            "toc": [(k, (o.label, o.title) if k == "chap" else (o.label, o.text)) for k, o in toc],
            "figs": [(b.label, b.path) for c, b in figs], "tabs": [b.label for c, b in tabs]}
    return out, meta


def add_references(doc, order):
    p = doc.add_paragraph(style="Heading 1")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.page_break_before = True
    set_spacing(p, before=0, after=25)
    style_run(p.add_run("References"), 16)
    for key, n in sorted(order.items(), key=lambda kv: kv[1]):
        q = doc.add_paragraph()
        q.alignment = WD_ALIGN_PARAGRAPH.LEFT
        q.paragraph_format.left_indent = Twips(567); q.paragraph_format.first_line_indent = Twips(-567)
        q.paragraph_format.tab_stops.add_tab_stop(Twips(567))
        set_spacing(q, after=4)
        add_runs(q, f"[{n}]\t{REFS[key]['text']}", size=11)


# ----------------------------------------------------------------------------------------------- render + page map
def render_pdf(docx: Path) -> Path:
    subprocess.run(["/opt/homebrew/bin/soffice", "--headless", "--convert-to", "pdf", "--outdir", str(docx.parent), str(docx)],
                   check=True, capture_output=True, timeout=300)
    return docx.with_suffix(".pdf")


def page_texts(pdf: Path) -> list[str]:
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout).group(1))
    out = []
    for i in range(1, n + 1):
        t = subprocess.run(["pdftotext", "-f", str(i), "-l", str(i), "-layout", str(pdf), "-"], capture_output=True, text=True).stdout
        out.append(re.sub(r"\s+", " ", t).strip())
    return out


def find_pages(pdf: Path, meta: dict) -> dict:
    T = page_texts(pdf)
    norm = lambda s: re.sub(r"\s+", " ", strip_markup(s)).strip()  # noqa: E731
    # first main-matter page = first page starting with "Chapter 1"
    main0 = next(i for i, t in enumerate(T) if t.startswith("Chapter 1 "))
    disp = lambda i: (str(i - main0 + 1) if i >= main0 else roman(i + 1))  # noqa: E731
    pages = {}
    for key, head in (("lof", "List of Figures"), ("lot", "List of Tables"), ("abbr", "List of Abbreviations and Symbols")):
        i = next(i for i, t in enumerate(T) if t.startswith(head) and i < main0)
        pages[key] = disp(i)
    cur = main0
    for kind, (lab, txt) in meta["toc"]:
        if kind == "chap":
            word = "Appendix" if lab.isalpha() else "Chapter"
            if word == "Appendix" and "refs" not in pages:
                ri = next(i for i in range(cur, len(T)) if T[i].startswith("References"))
                pages["refs"] = disp(ri); cur = ri
            cur = next(i for i in range(cur, len(T)) if T[i].startswith(f"{word} {lab} "))
            pages[f"chap:{lab}"] = disp(cur)
        else:
            target = norm(f"{lab} {txt}")[:60]
            hit = next((i for i in range(cur, len(T)) if target in T[i]), None)
            if hit is None:
                hit = next((i for i in range(cur, len(T)) if norm(f"{lab} {txt}")[:25] in T[i]), cur)
            pages[f"sec:{lab}"] = disp(hit); cur = hit
    for lab, _ in meta["figs"]:
        pages[f"fig:{lab}"] = disp(next(i for i in range(main0, len(T)) if f"Figure {lab}:" in T[i]))
    for lab in meta["tabs"]:
        pages[f"tab:{lab}"] = disp(next(i for i in range(main0, len(T)) if f"Table {lab}:" in T[i]))
    if "refs" not in pages:
        pages["refs"] = disp(next(i for i in range(main0, len(T)) if T[i].startswith("References")))
    pages["_n_pdf_pages"] = len(T)
    pages["_main_start_index"] = main0
    ap = [i for i, t in enumerate(T) if t.startswith("Appendix A ")]
    pages["_appendix_start_index"] = ap[0] if ap else len(T)
    return pages


def main():
    out, meta = build()
    pdf = render_pdf(out)
    pages = find_pages(pdf, meta)
    out, meta = build(pages)
    pdf = render_pdf(out)
    pages2 = find_pages(pdf, meta)
    changed = {k: (pages[k], pages2[k]) for k in pages if not k.startswith("_") and pages[k] != pages2[k]}
    if changed:
        out, meta = build(pages2)
        pdf = render_pdf(out)
        pages2 = find_pages(pdf, meta)
    n, a = pages2["_n_pdf_pages"], pages2["_appendix_start_index"]
    log = {"pdf_pages_total": n, "pages_before_appendices": a, "main_start_index": pages2["_main_start_index"],
           "n_references": len(meta["cite_order"]), "n_figures": len(meta["figs"]), "n_tables": len(meta["tabs"]),
           "page_changes_between_passes": changed, "cite_order": meta["cite_order"]}
    (OUTDIR / "build_log.json").write_text(json.dumps(log, indent=1))
    print(json.dumps({k: v for k, v in log.items() if k != "cite_order"}, indent=1))


if __name__ == "__main__":
    sys.exit(main())
