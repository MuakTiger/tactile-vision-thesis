#!/usr/bin/env python3
"""개정판 원고(졸업논문_개정판.md) → 학과 양식 docx.

원고는 일반 마크다운으로 쓰고, 이 스크립트가 ../양식/build_docx_D.py 가 읽는 형식으로
바꾼 뒤 그 스크립트의 build()를 그대로 부른다. build_docx_D.py 는 고치지 않는다.

사용:  python3 build.py            # 같은 폴더에 졸업논문_개정판.docx 를 만든다
       soffice --headless --convert-to pdf 졸업논문_개정판.docx   # 미리보기 PDF

필요: Pillow (JPG 사진의 크기를 읽고 줄일 때 쓴다)
"""
from __future__ import annotations

import importlib.util
import io
import re
import shutil
import sys
import zipfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE / "졸업논문_개정판.md"
OUT = HERE / "졸업논문_개정판.docx"
TMP = HERE / "_build"
HEADER = {" 0 ": " 17 ", "(20○○)": "(2026)"}  # 머리말의 회차·연도
FIG_WIDTH_CM = {"fig1_assembled": 4.6}  # 나머지는 한 단 폭 7.2 cm
PHOTO_MAX_PX = 1200  # 사진(JPG)의 가로 화소 상한. 7.2 cm 폭에서 약 420 dpi
JPEG_MAGIC = b"\xff\xd8"

sys.dont_write_bytecode = True  # 양식 폴더에 __pycache__ 를 남기지 않는다
spec = importlib.util.spec_from_file_location("bd", HERE.parent / "양식" / "build_docx_D.py")
bd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bd)

_png_size = bd.png_size


def image_size(data: bytes):
    """build_docx_D.py 의 png_size 를 대신한다. JPG 도 받는다."""
    if data[:2] == JPEG_MAGIC:
        return Image.open(io.BytesIO(data)).size
    return _png_size(data)


def stage_image(path: str) -> str:
    """그림을 _build 로 옮긴다. JPG 사진은 PHOTO_MAX_PX 로 줄이고, PNG 는 그대로 둔다."""
    src = HERE / path
    dst = TMP / src.name
    if src.suffix.lower() in (".jpg", ".jpeg"):
        im = Image.open(src).convert("RGB")
        if im.width > PHOTO_MAX_PX:
            im = im.resize((PHOTO_MAX_PX, round(im.height * PHOTO_MAX_PX / im.width)), Image.LANCZOS)
        im.save(dst, quality=90)
    else:
        shutil.copyfile(src, dst)
    return dst.name


def convert(md: str) -> str:
    lines = md.splitlines()
    title_ko = lines[0].lstrip("# ").strip()
    rest = lines[1:]
    # 제목 아래 세 줄(영문 제목, 저자, 소속)
    head = [l for l in rest[: rest.index("## 요 약")] if l.strip()]
    title_en, author, affil = head[0], head[1], head[2]
    body = rest[rest.index("## 요 약"):]

    out = ["---", f"title_ko: {title_ko}", f"title_en: {title_en}",
           f"authors_ko: {author}", f"authors_en: {affil}", "---", ""]
    i = 0
    while i < len(body):
        l = body[i]
        # 절 제목
        m = re.match(r"## (Ⅰ|Ⅱ|Ⅲ|Ⅳ|Ⅴ)\. (\S) (\S)$", l)
        if m:
            l = f"## {m.group(1)}. {m.group(2)}  {m.group(3)}"
        if l.startswith("**주제어 :**") or l.startswith("**Keywords :**"):
            l = l.replace(" :**", ":**")
        # 그림: 그림 줄 + 빈 줄 + **[그림 n]** 설명
        m = re.match(r"!\[.*\]\((.+)\)$", l)
        if m:
            cm = re.match(r"\*\*(\[그림 \d+\])\*\* (.*)", body[i + 2])
            w = FIG_WIDTH_CM.get(Path(m.group(1)).stem, 7.2)
            out += [f"![{cm.group(1)} {cm.group(2)}]({stage_image(m.group(1))}){{width={w}}}", ""]
            i += 3
            continue
        # 표 제목: **[표 n]** 제목 + 빈 줄 + 표
        m = re.match(r"\*\*(\[표 \d+\])\*\* (.*)", l)
        if m:
            out.append(f"{m.group(1)} {m.group(2)}")
            i += 2
            continue
        # 표 안의 구분 줄
        m = re.match(r"\| \*\*(.+?)\*\* \|[ |]*$", l)
        if m:
            l = f"| § {m.group(1)} |" + " |" * (l.count("|") - 2)
        # 목록은 한 줄이 한 문단
        if re.match(r"(- |\d+\) )", l):
            out += [re.sub(r"^- ", "· ", l), ""]
            i += 1
            continue
        out.append(l)
        i += 1
    text = "\n".join(out)
    return text.replace("d_far", "d<sub>far</sub>").replace("c_y", "c<sub>y</sub>")


def postprocess(path: Path):
    """머리말의 회차·연도를 채우고, JPG 그림의 확장자와 형식 선언을 바로잡는다."""
    buf = io.BytesIO()
    with zipfile.ZipFile(path) as zin:
        jpgs = {n for n in zin.namelist()
                if n.startswith("word/media/") and zin.read(n)[:2] == JPEG_MAGIC}
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                name = item.filename
                if re.fullmatch(r"word/header\d*\.xml", name):
                    s = data.decode("utf-8")
                    for a, b in HEADER.items():
                        s = s.replace(f">{a}<", f">{b}<")
                    data = s.encode("utf-8")
                elif name == "word/_rels/document.xml.rels":
                    s = data.decode("utf-8")
                    for j in jpgs:
                        base = j.split("/")[-1]
                        s = s.replace(f'media/{base}"', f'media/{base[:-4]}.jpg"')
                    data = s.encode("utf-8")
                elif name == "[Content_Types].xml" and jpgs:
                    s = data.decode("utf-8")
                    if 'Extension="jpg"' not in s:
                        s = s.replace('<Default Extension="xml"',
                                      '<Default Extension="jpg" ContentType="image/jpeg"/><Default Extension="xml"')
                    data = s.encode("utf-8")
                elif name in jpgs:
                    name = name[:-4] + ".jpg"
                zout.writestr(name, data)
    path.write_bytes(buf.getvalue())


def main():
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir()
    tmp_md = TMP / "manuscript.md"
    tmp_md.write_text(convert(SRC.read_text(encoding="utf-8")), encoding="utf-8")
    bd.HEADER_BLANKS = ()
    bd.png_size = image_size
    bd.build(tmp_md, OUT)
    postprocess(OUT)
    shutil.rmtree(TMP)


if __name__ == "__main__":
    main()
