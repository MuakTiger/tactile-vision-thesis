#!/usr/bin/env python3
"""
거리 정확도 사진에 표적(흰 상자 앞면) 영역을 손으로 표시한다 → rois.csv

자동 검출은 쓰지 않는다(2026-10-17 시험: 가까운 거리에서 바닥을, 그늘에서는 상자를 못 잡음).
좌표는 원본 1280×720 픽셀 기준이다. 장치 전처리(가운데 1280×698 → 924×504)로의 변환은 분석 쪽에서 한다.

사용
  python thesis/analysis/annotate_roi.py thesis/analysis/data/raw/distance_20261017
  (폴더 아래 각 장소 폴더의 *.png 를 차례로 띄운다. 이미 표시한 사진은 건너뛴다 → 중간에 끊어도 이어서 가능)

키 (사진 한 장마다)
  마우스 드래그   상자 앞면을 사각형으로 감싼다 (모서리 바깥 배경이 들어가지 않게 살짝 안쪽으로)
  space / Enter  확정하고 다음 사진
  c              표적 없음으로 기록 (숫자 종이 사진 등) → x,y,w,h = -1
  Ctrl+C (터미널) 중단. 그때까지 표시한 건 저장돼 있다
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import cv2

FIELDS = ["site", "file", "distance_m", "x", "y", "w", "h"]
WIN = "ROI - drag box, SPACE ok, c = no target"


def distance_of(name: str) -> str:
    # outdoor_1p5m_03_105303.png → 1.5
    return name.split("_")[1].rstrip("m").replace("p", ".")


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    root = Path(sys.argv[1]).expanduser()
    out = root / "rois.csv"
    done: dict[tuple[str, str], dict] = {}
    if out.exists():
        with out.open(encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                done[(r["site"], r["file"])] = r

    todo = [(d.name, p) for d in sorted(root.iterdir()) if d.is_dir() and not d.name.startswith("_")
            for p in sorted(d.glob("*.png"))]
    print(f"사진 {len(todo)}장, 이미 표시 {len(done)}장 → {out}")

    def save() -> None:
        with out.open("w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=FIELDS)
            wr.writeheader()
            wr.writerows(done[k] for k in sorted(done))

    cv2.namedWindow(WIN, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    try:
        for i, (site, p) in enumerate(todo, 1):
            if (site, p.name) in done:
                continue
            img = cv2.imread(str(p))
            cv2.setWindowTitle(WIN, f"[{i}/{len(todo)}] {site}/{p.name}  ({distance_of(p.name)} m)  "
                                    "drag box, SPACE ok, c = no target")
            x, y, w, h = cv2.selectROI(WIN, img, showCrosshair=True, fromCenter=False)
            if w == 0 or h == 0:
                x = y = w = h = -1
            done[(site, p.name)] = {"site": site, "file": p.name, "distance_m": distance_of(p.name),
                                    "x": x, "y": y, "w": w, "h": h}
            save()
            print(f"{site}/{p.name}: {x},{y},{w},{h}")
    except KeyboardInterrupt:
        print("중단 — 저장됨")
    finally:
        cv2.destroyAllWindows()
    print(f"끝 — {len(done)}/{len(todo)}장 표시, {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
