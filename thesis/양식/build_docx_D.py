#!/usr/bin/env python3
"""원고 md → 학과 '졸업논문 양식 1번' docx — D판용 복사본 (2026-10-19, iMac).

build_docx.py(원본, 고치지 않음)와 같고 다음 세 가지만 더한다. ① 머리말의 사용자만 채울 칸
('제 0 회'의 0, '(20○○)')에 노란 형광을 칠해 눈에 띄게 한다. 글자는 양식 그대로 둔다.
② 표 바로 다음 본문 문단에 위 간격(5 pt)을 주어 표의 아래 선과 글이 붙지 않게 하고,
③ 10줄 이하의 작은 표는 줄마다 '다음 문단과 함께'를 걸어 한 단 안에 모이게 한다(표 뒤 '주:'도 함께).

원본 설명:

양식 파일(같은 폴더의 졸업논문참고양식.docx)을 그대로 열어 본문(word/document.xml의 body)만 바꾼다.
머리말·꼬리말, 1단(제목·초록) → 2단(본문) 구역 설정, 글꼴·크기·간격은 양식의 예시 문단과 같게 쓴다.
표준 라이브러리만 쓴다(python-docx 불필요).

사용:  python build_docx_D.py ../졸업논문_D_새설계판.md  [-o 출력.docx]
       출력 기본값은 md와 같은 이름의 .docx

md 규칙 (이 원고들에서 쓰는 것만)
  - 맨 앞 '>' 줄(작성 메모)은 넣지 않는다.
  - '---' 사이의 머리 정보: title_ko, title_en, authors_ko, authors_en
  - '## 요약' / '## Abstract' : 초록(1단). 본문의 **목적:** 같은 굵은 꼬리표, **주제어:** / **Keywords:** 줄
  - '## Ⅰ. 서  론' 등: 절 제목(2단 시작),  '### 2.1 …': 소절 제목
  - '![[그림 n] 설명](경로){width=7.2}' : 그림(가로 cm) + 아래 설명
  - '[표 n] 제목' 다음 줄부터 '|' 표: 위 제목 + 표. 첫 칸이 '§ '로 시작하는 줄은 가로로 합친 구분 줄.
    표 바로 뒤 '주:'로 시작하는 문단은 표 주석.
  - '## 참고문헌' 아래 '[n] …' : 참고문헌(내어쓰기, doi 주소는 링크)
  - 글 안: **굵게**, *기울임*, <sub>아래</sub>, <sup>위</sup>, 〔채울 곳〕(노란 형광)
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import struct
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE / "졸업논문참고양식.docx"
COL_W_TWIPS = 4229  # 2단 한 단 폭: (11906 − 2×1440 − 567) / 2
GOTHIC = '<w:rFonts w:ascii="Arial" w:eastAsia="맑은 고딕" w:hAnsi="Arial"/>'
REL_IMG = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
REL_LINK = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"


# ───────────────────────── 글 조각(run) ─────────────────────────
class Doc:
    def __init__(self):
        self.rels: list[str] = []
        self.media: list[tuple[str, bytes]] = []
        self.rid = 1000
        self.pic_id = 100

    def new_rid(self):
        self.rid += 1
        return f"rId{self.rid}"


def rpr(bold=False, italic=False, size=None, gothic=False, color=None, highlight=None, vert=None, underline=False):
    x = []
    if gothic:
        x.append(GOTHIC)
    if bold:
        x.append("<w:b/><w:bCs/>")
    if italic:
        x.append("<w:i/><w:iCs/>")
    if color:
        x.append(f'<w:color w:val="{color}"/>')
    if size:
        x.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if highlight:
        x.append(f'<w:highlight w:val="{highlight}"/>')
    if underline:
        x.append('<w:u w:val="single"/>')
    if vert:
        x.append(f'<w:vertAlign w:val="{vert}"/>')
    return f"<w:rPr>{''.join(x)}</w:rPr>" if x else ""


def run(text, **kw):
    if not text:
        return ""
    return f'<w:r>{rpr(**kw)}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


TOKEN = re.compile(r"(\*\*.+?\*\*|<sub>.+?</sub>|<sup>.+?</sup>|〔[^〕]*〕|https?://[^\s<>]+|(?<![*\w])\*[^*\s][^*]*?\*(?![*\w]))")


def inline(doc: Doc, text: str, size=18, gothic=False, bold=False, links=False):
    """**굵게**, *기울임*, <sub>, <sup>, 〔 〕, URL 처리."""
    out = []
    pos = 0
    for m in TOKEN.finditer(text):
        if m.start() > pos:
            out.append(run(text[pos:m.start()], size=size, gothic=gothic, bold=bold))
        t = m.group(0)
        if t.startswith("**"):
            out.append(inline(doc, t[2:-2], size=size, gothic=gothic, bold=True, links=links))
        elif t.startswith("<sub>"):
            out.append(run(t[5:-6], size=size, gothic=gothic, bold=bold, vert="subscript"))
        elif t.startswith("<sup>"):
            out.append(run(t[5:-6], size=size, gothic=gothic, bold=bold, vert="superscript"))
        elif t.startswith("〔"):
            out.append(run(t, size=size, gothic=gothic, bold=bold, highlight="yellow"))
        elif t.startswith("http"):
            url = t.rstrip(".,;)")
            tail = t[len(url):]
            if links:
                rid = doc.new_rid()
                doc.rels.append(f'<Relationship Id="{rid}" Type="{REL_LINK}" Target="{escape(url)}" TargetMode="External"/>')
                out.append(f'<w:hyperlink r:id="{rid}" w:history="1">'
                           f'{run(url, size=size, color="1155CC", underline=True)}</w:hyperlink>')
            else:
                out.append(run(url, size=size, gothic=gothic, bold=bold))
            out.append(run(tail, size=size, gothic=gothic, bold=bold))
        else:  # *기울임*
            out.append(run(t[1:-1], size=size, gothic=gothic, bold=bold, italic=True))
        pos = m.end()
    if pos < len(text):
        out.append(run(text[pos:], size=size, gothic=gothic, bold=bold))
    return "".join(out)


def para(runs, jc=None, before=None, after=None, left=None, right=None, first=None, hanging=None,
         line=None, keep_next=False, keep_lines=False, extra=""):
    p = []
    if keep_next:
        p.append("<w:keepNext/>")
    if keep_lines:
        p.append("<w:keepLines/>")
    p.append(extra)
    sp = []
    if before is not None:
        sp.append(f'w:before="{before}"')
    if after is not None:
        sp.append(f'w:after="{after}"')
    if line is not None:
        sp.append(f'w:line="{line}" w:lineRule="auto"')
    if sp:
        p.append(f"<w:spacing {' '.join(sp)}/>")
    ind = []
    if left is not None:
        ind.append(f'w:left="{left}"')
    if right is not None:
        ind.append(f'w:right="{right}"')
    if first is not None:
        ind.append(f'w:firstLine="{first}"')
    if hanging is not None:
        ind.append(f'w:hanging="{hanging}"')
    if ind:
        p.append(f"<w:ind {' '.join(ind)}/>")
    if jc:
        p.append(f'<w:jc w:val="{jc}"/>')
    return f"<w:p><w:pPr>{''.join(p)}</w:pPr>{runs}</w:p>"


# ───────────────────────── 그림 ─────────────────────────
def png_size(data: bytes):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("PNG만 지원")
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def figure(doc: Doc, md_dir: Path, caption: str, path: str, width_cm: float):
    data = (md_dir / path).read_bytes()
    w, h = png_size(data)
    name = f"image{len(doc.media) + 1}.png"
    doc.media.append((name, data))
    rid = doc.new_rid()
    doc.rels.append(f'<Relationship Id="{rid}" Type="{REL_IMG}" Target="media/{name}"/>')
    cx = int(width_cm * 360000)
    cy = int(cx * h / w)
    doc.pic_id += 1
    pid = doc.pic_id
    drawing = (
        f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>'
        f'<wp:docPr id="{pid}" name="그림 {pid}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="{pid}" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        f'</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>'
    )
    img_p = para(drawing, jc="center", before=80, after=40, keep_next=True)
    cap_p = para(inline(doc, caption, size=16, gothic=True), jc="center", after=120)
    return img_p + cap_p


# ───────────────────────── 표 ─────────────────────────
def split_row(line: str):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    cells = re.split(r"(?<!\\)\|", line)
    return [c.strip().replace("\\|", "|") for c in cells]


EM = 150  # 표 글자 7.5 pt 한 칸(twips)


def char_em(ch: str) -> float:
    o = ord(ch)
    if 0xAC00 <= o <= 0xD7AF or 0x1100 <= o <= 0x11FF or 0x2E80 <= o <= 0x9FFF or 0x2190 <= o <= 0x21FF:
        return 1.0  # 한글·한자·화살표
    if ch == " ":
        return 0.25
    if ch in ".,:;|!il'":
        return 0.3
    if ch in "()[]-–/":
        return 0.36
    if ch in "%MW":
        return 0.85
    if ch.isupper():
        return 0.66
    return 0.52


def text_twips(s: str, bold=False) -> float:
    s = re.sub(r"<[^>]+>", "", s).replace("**", "")
    return sum(char_em(c) for c in s) * EM * (1.07 if bold else 1.0)


def is_numeric_col(cells) -> bool:
    vals = [c for c in cells if c]
    if not vals:
        return True
    num = sum(1 for c in vals if re.fullmatch(r"[\d.,+−\-–~% ()×/→]*", c) or text_twips(c) <= 4 * EM)
    return num >= 0.7 * len(vals)


KEEP_TOGETHER_MAX_ROWS = 10  # D판 추가: 이 줄 수 이하의 표는 나누지 않는다


def table(doc: Doc, lines: list[str], keep_last: bool = False):
    rows = [split_row(l) for l in lines if not re.match(r"^\s*\|?\s*:?-{3,}", l)]
    header, body = rows[0], rows[1:]
    n = len(header)
    plain = [(r + [""] * n)[:n] for r in body if not r[0].startswith("§")]
    # 열 폭: 각 열의 '줄바꿈 없는 폭'(pref)과 '가장 긴 낱말 폭'(minw)으로 정한다(웹 표 자동 배치와 같은 방식).
    # 숫자 칸은 낱말을 쪼개지 않고, 첫 열과 머리글은 띄어쓰기에서 줄을 바꿀 수 있다.
    pad = 2 * 50 + 50
    numeric = [False] + [is_numeric_col([r[i] for r in plain]) for i in range(1, n)]
    pref, minw = [], []
    for i in range(n):
        col = [header[i]] + [r[i] for r in plain]
        pref.append(max(text_twips(c, bold=(k == 0)) for k, c in enumerate(col)) + pad)
        toks = [t for k, c in enumerate(col) for t in (c.split(" ") if (k == 0 or not numeric[i]) else [c]) if t]
        minw.append((max(text_twips(t, bold=True) for t in toks) if toks else 0) + pad)
    W = COL_W_TWIPS
    if sum(pref) <= W:
        widths = [p_ * W / sum(pref) for p_ in pref]
    elif sum(minw) <= W:
        room = W - sum(minw)
        slack = [max(p_ - m_, 0.0) for p_, m_ in zip(pref, minw)]
        widths = [m_ + (room * sl / sum(slack) if sum(slack) else 0) for m_, sl in zip(minw, slack)]
    else:
        widths = [m_ * W / sum(minw) for m_ in minw]
    widths = [int(w) for w in widths]
    widths[-1] = W - sum(widths[:-1])
    align = ["center" if numeric[i] else "left" for i in range(n)]
    align[0] = "left"

    together = len(rows) <= KEEP_TOGETHER_MAX_ROWS  # 머리줄 포함 줄 수

    def cell(txt, w, bold=False, jc="center", span=1, shade=None, bottom=None, keep=False):
        tcpr = [f'<w:tcW w:w="{w}" w:type="dxa"/>']
        if span > 1:
            tcpr.append(f'<w:gridSpan w:val="{span}"/>')
        if bottom:
            tcpr.append(f'<w:tcBorders><w:bottom w:val="single" w:sz="{bottom}" w:space="0" w:color="000000"/></w:tcBorders>')
        if shade:
            tcpr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>')
        tcpr.append('<w:vAlign w:val="center"/>')
        p = para(inline(doc, txt, size=15, bold=bold), jc=jc, before=10, after=10, line=216, keep_next=keep)
        return f"<w:tc><w:tcPr>{''.join(tcpr)}</w:tcPr>{p}</w:tc>"

    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    x = [
        '<w:tbl><w:tblPr><w:tblW w:w="%d" w:type="dxa"/><w:jc w:val="center"/>'
        '<w:tblBorders><w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/></w:tblBorders>'
        '<w:tblLayout w:type="fixed"/>'
        '<w:tblCellMar><w:top w:w="15" w:type="dxa"/><w:left w:w="50" w:type="dxa"/>'
        '<w:bottom w:w="15" w:type="dxa"/><w:right w:w="50" w:type="dxa"/></w:tblCellMar>'
        '<w:tblLook w:val="04A0" w:firstRow="1" w:lastRow="0" w:firstColumn="1" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/>'
        "</w:tblPr>" % COL_W_TWIPS,
        f"<w:tblGrid>{grid}</w:tblGrid>",
    ]
    x.append('<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>'
             + "".join(cell(header[i], widths[i], bold=True, jc=align[i], bottom=4, keep=together) for i in range(n))
             + "</w:tr>")
    for k, r in enumerate(body):
        keep = together and (k < len(body) - 1 or keep_last)
        if r[0].startswith("§"):
            x.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>'
                     + cell(r[0].lstrip("§ ").strip(), COL_W_TWIPS, bold=True, jc="left", span=n, shade="F2F2F2", keep=keep)
                     + "</w:tr>")
            continue
        r = (r + [""] * n)[:n]
        x.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>'
                 + "".join(cell(r[i], widths[i], jc=align[i], keep=keep) for i in range(n))
                 + "</w:tr>")
    x.append("</w:tbl>")
    return "".join(x)


# ───────────────────────── 문서 조립 ─────────────────────────


def build(md_path: Path, out_path: Path):
    md = md_path.read_text(encoding="utf-8")
    lines = md.splitlines()
    # 작성 메모(>) 건너뛰기
    i = 0
    while i < len(lines) and (lines[i].startswith(">") or not lines[i].strip()):
        i += 1
    # 머리 정보
    meta = {}
    if i < len(lines) and lines[i].strip() == "---":
        i += 1
        while lines[i].strip() != "---":
            if ":" in lines[i]:
                k, v = lines[i].split(":", 1)
                meta[k.strip()] = v.strip()
            i += 1
        i += 1
    rest = lines[i:]

    # 블록 나누기(빈 줄 기준, 표는 연속 줄)
    blocks: list[list[str]] = []
    cur: list[str] = []
    for l in rest:
        if not l.strip():
            if cur:
                blocks.append(cur)
                cur = []
            continue
        if l.startswith("#") and cur:
            blocks.append(cur)
            cur = []
        cur.append(l)
        if l.startswith("#"):
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)

    doc = Doc()
    out = []
    # 제목·저자 (양식 0~3번 문단)
    out.append(para(run(meta["title_ko"], bold=True, size=38, gothic=True), jc="center", before=200, after=60))
    out.append(para(inline(doc, meta["title_en"], size=26), jc="center", after=200))
    out.append(para(inline(doc, meta["authors_ko"], size=22), jc="center", after=20))
    out.append(para(inline(doc, meta["authors_en"], size=19), jc="center", after=220))

    mode = None
    first_body_heading = True
    after_table = False  # 바로 앞 블록이 표였는가 (D판 추가)
    md_dir = md_path.parent
    tpl = zipfile.ZipFile(TEMPLATE)
    tdoc = tpl.read("word/document.xml").decode("utf-8")
    sect1 = re.search(r"<w:sectPr\b.*?</w:sectPr>", tdoc, re.S).group(0)
    sect_final = list(re.finditer(r"<w:sectPr\b.*?</w:sectPr>", tdoc, re.S))[-1].group(0)

    for bi, b in enumerate(blocks):
        head = b[0]
        nxt_note = bi + 1 < len(blocks) and blocks[bi + 1][0].strip().startswith("주:")
        if head.startswith("## "):
            title = head[3:].strip()
            if title in ("요약", "요 약"):
                mode = "abs_ko"
                out.append(para(run("요    약", bold=True, size=20, gothic=True), jc="center", after=60))
                continue
            if title == "Abstract":
                mode = "abs_en"
                out.append(para(run("Abstract", bold=True, size=20, gothic=True), jc="center", before=60, after=60))
                continue
            if first_body_heading:  # 1단 구역 끝 → 2단 시작
                out.append(f"<w:p><w:pPr>{sect1}</w:pPr></w:p>")
                first_body_heading = False
            mode = "refs" if title == "참고문헌" else "body"
            out.append(para(run(title, bold=True, size=21, gothic=True), jc="center", before=200, after=80, keep_next=True))
            continue
        if head.startswith("### "):
            out.append(para(run(head[4:].strip(), bold=True, gothic=True), before=120, after=40, keep_next=True))
            continue
        text = " ".join(l.strip() for l in b)

        if mode in ("abs_ko", "abs_en"):
            m = re.match(r"\*\*(주제어|Keywords):\*\*\s*(.*)", text)
            if m:
                lab = "주제어 : " if m.group(1) == "주제어" else "Keywords : "
                out.append(para(run(lab, bold=True, size=18, gothic=(mode == "abs_ko")) + inline(doc, m.group(2), size=18),
                                left=360, right=360, after=160))
            else:
                # 꼬리표(**목적:**)는 국문은 고딕, 영문은 본문 글꼴 굵게
                parts = re.split(r"(\*\*[^*]+:\*\*)", text)
                runs = []
                for ptxt in parts:
                    if re.fullmatch(r"\*\*[^*]+:\*\*", ptxt):
                        runs.append(run(ptxt[2:-2] + " ", bold=True, size=18, gothic=(mode == "abs_ko")))
                    elif ptxt.strip():
                        runs.append(inline(doc, ptxt.strip() + " ", size=18))
                out.append(para("".join(runs), jc="both", left=360, right=360, after=80))
            continue

        if mode == "refs":
            for l in b:
                out.append(para(inline(doc, l.strip(), size=16, links=True), after=30, line=220, left=360, hanging=360))
            continue

        # 본문
        m = re.match(r"!\[(.+)\]\(([^)]+)\)(\{width=([\d.]+)\})?$", text)
        if m:
            out.append(figure(doc, md_dir, m.group(1), m.group(2), float(m.group(4) or 7.2)))
            after_table = False
            continue
        tl = [l for l in b[1:] if l.strip().startswith("|")]
        if re.match(r"\[표 \d+\] ", head) and tl:  # 표 제목 줄 바로 아래에 표가 이어질 때만
            out.append(para(inline(doc, head.strip(), size=16, gothic=True), jc="center", before=120, after=60, keep_next=True))
            out.append(table(doc, tl, keep_last=nxt_note))
            after_table = True
            continue
        if head.strip().startswith("|"):
            out.append(table(doc, [l for l in b if l.strip().startswith("|")], keep_last=nxt_note))
            after_table = True
            continue
        if text.startswith("주:"):
            out.append(para(inline(doc, text, size=14), jc="both", before=30, after=120))
            after_table = False
            continue
        out.append(para(inline(doc, text, size=18), jc="both", after=40, first=180, before=100 if after_table else None))
        after_table = False

    body = "".join(out) + sect_final
    new_doc = re.sub(r"<w:body>.*</w:body>", lambda _: f"<w:body>{body}</w:body>", tdoc, flags=re.S)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        for item in tpl.infolist():
            data = tpl.read(item.filename)
            if item.filename == "word/document.xml":
                data = new_doc.encode("utf-8")
            elif re.fullmatch(r"word/header\d*\.xml", item.filename):
                data = highlight_header(data.decode("utf-8")).encode("utf-8")
            elif item.filename == "word/_rels/document.xml.rels":
                s = data.decode("utf-8")
                # 양식 예시의 참고문헌 링크는 지우고 새 관계를 더한다
                s = re.sub(r'<Relationship [^>]*relationships/hyperlink"[^>]*/>', "", s)
                s = s.replace("</Relationships>", "".join(doc.rels) + "</Relationships>")
                data = s.encode("utf-8")
            elif item.filename == "[Content_Types].xml":
                s = data.decode("utf-8")
                if 'Extension="png"' not in s:
                    s = s.replace("<Default Extension=\"xml\"", '<Default Extension="png" ContentType="image/png"/><Default Extension="xml"')
                data = s.encode("utf-8")
            elif item.filename == "docProps/core.xml":
                s = data.decode("utf-8")
                now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                s = re.sub(r"<dc:creator>.*?</dc:creator>", "<dc:creator>오형준</dc:creator>", s)
                s = re.sub(r"<cp:lastModifiedBy>.*?</cp:lastModifiedBy>", "<cp:lastModifiedBy>오형준</cp:lastModifiedBy>", s)
                s = re.sub(r"(<dcterms:modified[^>]*>).*?(</dcterms:modified>)", rf"\g<1>{now}\g<2>", s)
                if "<dc:title>" not in s:
                    s = s.replace("<dc:creator>", f"<dc:title>{escape(meta['title_ko'])}</dc:title><dc:creator>")
                data = s.encode("utf-8")
            z.writestr(item, data)
        for name, data in doc.media:
            z.writestr(f"word/media/{name}", data)
    print("저장:", out_path)


HEADER_BLANKS = (" 0 ", "(20○○)")  # 머리말에서 사용자가 회차·연도를 채울 칸


def highlight_header(xml: str) -> str:
    """머리말 run 중 글자가 HEADER_BLANKS인 것에 노란 형광(w:highlight)을 더한다. 글자는 바꾸지 않는다."""
    def fix(m):
        r = m.group(0)
        t = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", r))
        if t in HEADER_BLANKS and "<w:highlight" not in r:
            r = r.replace("</w:rPr>", '<w:highlight w:val="yellow"/></w:rPr>', 1)
        return r
    return re.sub(r"<w:r\b.*?</w:r>", fix, xml, flags=re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("md")
    ap.add_argument("-o", "--out")
    a = ap.parse_args()
    md = Path(a.md).resolve()
    out = Path(a.out).resolve() if a.out else md.with_suffix(".docx")
    build(md, out)


if __name__ == "__main__":
    sys.exit(main())
