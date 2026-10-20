"""장치 기구 3D 모델 그림 — 촉각 패드와 핀 구동부 STL을 한 단 폭으로 그린다 (2026-10-19, iMac).

자료: 하드웨어 저장소(tactile-vision-device)의 STL 그대로. 치수는 STL에서 잰 값만 쓴다.
  hardware/full/7_22 set_final.stl                 베이스판 1 + 서보 유닛 24 (독립 바디 25개)
  hardware/assembly/SG90 and Rack and Pinion.stl   SG90 + 브래킷 + 피니언 + 랙
착용형 하우징(print_plate_nested.stl)은 설계만 하고 실험에 쓰지 않아 넣지 않는다.

matplotlib 3D는 면을 앞뒤 순서로만 겹쳐 그려 가려짐이 틀리므로, 깊이 버퍼로 직접 그린다
(정사영, 면 단위 음영, 법선·깊이가 끊기는 곳에 윤곽선).

실행: python hw_figure.py [하드웨어 폴더]   → figures/final/fig_hw_cad.png
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures" / "final"
HW = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Documents/kiro/tactile-vision-device/hardware"
COL_W = 2.9  # inch, 한 단 7.46 cm 안
BLUE, ORANGE, GREEN, GRAY = "#2a78d6", "#e8613a", "#1b9e77", "#555555"
SERVO, PLATE = "#5b6b84", "#d3d9e1"

plt.rcParams.update({
    "font.family": ["Apple SD Gothic Neo", "Nanum Gothic", "DejaVu Sans"],
    "font.size": 7, "savefig.dpi": 300, "axes.unicode_minus": False,
})


# ───────────────────────── STL 읽기 ─────────────────────────
def load_stl(p: Path) -> np.ndarray:
    """바이너리 STL → (삼각형 수, 3, 3)."""
    b = p.read_bytes()
    n = int(np.frombuffer(b[80:84], "<u4")[0])
    dt = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    return np.frombuffer(b[84:], dt, count=n)["v"].astype(float)


def bodies(tri: np.ndarray) -> list[np.ndarray]:
    """정점을 공유하는 삼각형끼리 묶어 독립 바디로 나눈다."""
    uv, inv = np.unique(np.round(tri.reshape(-1, 3), 3), axis=0, return_inverse=True)
    inv = inv.reshape(-1, 3)
    parent = np.arange(len(uv))

    def find(x):
        r = x
        while parent[r] != r:
            r = parent[r]
        while parent[x] != r:
            parent[x], x = r, parent[x]
        return r

    for a, b, c in inv:
        ra = find(a)
        parent[find(b)] = ra
        parent[find(c)] = ra
    lab = np.array([find(i) for i in range(len(uv))])[inv[:, 0]]
    return [tri[lab == i] for i in np.unique(lab)]


def size(t: np.ndarray) -> np.ndarray:
    v = t.reshape(-1, 3)
    return v.max(0) - v.min(0)


# ───────────────────────── 깊이 버퍼 렌더 ─────────────────────────
class View:
    """정사영 카메라. el·az는 matplotlib view_init과 같은 뜻(도)."""

    def __init__(self, el: float, az: float, px_per_mm: float, allv: np.ndarray, margin: int = 6):
        e, a = np.radians(el), np.radians(az)
        self.d = np.array([np.cos(e) * np.cos(a), np.cos(e) * np.sin(a), np.sin(e)])  # 장면 → 카메라
        self.r = np.array([-np.sin(a), np.cos(a), 0.0])
        self.u = np.cross(self.d, self.r)
        self.s = px_per_mm
        uv = self._uv(allv)
        self.o = uv.min(0) - margin
        self.w, self.h = (np.ceil(uv.max(0) - self.o) + margin).astype(int)

    def _uv(self, p):
        return np.c_[p @ self.r, -(p @ self.u)] * self.s

    def px(self, p):
        """3D 점 → 그림 좌표(열, 행)."""
        return self._uv(np.atleast_2d(p)) - self.o


def render(parts: list[tuple[np.ndarray, str]], view: View, ss: int = 3) -> np.ndarray:
    W, H = view.w * ss, view.h * ss
    zbuf = np.full((H, W), -np.inf)
    nbuf = np.zeros((H, W, 3))
    cbuf = np.ones((H, W, 3))
    bbuf = np.full((H, W), -1)
    L = 0.55 * view.d + 0.65 * view.u - 0.35 * view.r
    L /= np.linalg.norm(L)
    for bi, (tri, color) in enumerate(parts):
        rgb = np.array(matplotlib.colors.to_rgb(color))
        uv = (view._uv(tri.reshape(-1, 3)) - view.o).reshape(-1, 3, 2) * ss
        z = (tri.reshape(-1, 3) @ view.d).reshape(-1, 3)
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        ln = np.linalg.norm(n, axis=1)
        for k in np.nonzero(ln > 1e-9)[0]:
            nk = n[k] / ln[k]
            if nk @ view.d < 0:
                nk = -nk
            (x0, y0), (x1, y1), (x2, y2) = uv[k]
            den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
            if abs(den) < 1e-9:
                continue
            i0, i1 = int(max(np.floor(min(x0, x1, x2)), 0)), int(min(np.ceil(max(x0, x1, x2)), W - 1))
            j0, j1 = int(max(np.floor(min(y0, y1, y2)), 0)), int(min(np.ceil(max(y0, y1, y2)), H - 1))
            if i1 < i0 or j1 < j0:
                continue
            X, Y = np.meshgrid(np.arange(i0, i1 + 1) + 0.5, np.arange(j0, j1 + 1) + 0.5)
            l0 = ((y1 - y2) * (X - x2) + (x2 - x1) * (Y - y2)) / den
            l1 = ((y2 - y0) * (X - x2) + (x0 - x2) * (Y - y2)) / den
            l2 = 1 - l0 - l1
            m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            zz = l0 * z[k, 0] + l1 * z[k, 1] + l2 * z[k, 2]
            sub = zbuf[j0:j1 + 1, i0:i1 + 1]
            m &= zz > sub + 1e-6
            if not m.any():
                continue
            sub[m] = zz[m]
            nbuf[j0:j1 + 1, i0:i1 + 1][m] = nk
            shade = 0.42 + 0.58 * max(0.0, float(nk @ L))
            cbuf[j0:j1 + 1, i0:i1 + 1][m] = np.clip(rgb * shade + 0.10 * (1 - shade), 0, 1)
            bbuf[j0:j1 + 1, i0:i1 + 1][m] = bi
    # 윤곽선: 이웃 화소와 법선이 25° 넘게 다르거나, 깊이가 크게 끊기거나, 바디가 다른 곳
    edge = np.zeros((H, W), bool)
    cos_t = np.cos(np.radians(25))
    fg = bbuf >= 0
    for dy, dx in ((0, 1), (1, 0)):
        a = (slice(0, H - dy), slice(0, W - dx))
        b = (slice(dy, H), slice(dx, W))
        diff_b = bbuf[a] != bbuf[b]
        both = fg[a] & fg[b]
        diff_n = both & ((nbuf[a] * nbuf[b]).sum(-1) < cos_t)
        diff_z = both & (np.abs(zbuf[a] - zbuf[b]) > 1.2)
        e = diff_b | diff_n | diff_z
        edge[a] |= e
    img = cbuf.copy()
    img[edge] = img[edge] * 0.35
    # 다운샘플(계단 줄이기)
    img = img.reshape(view.h, ss, view.w, ss, 3).mean((1, 3))
    return img


# ───────────────────────── 그림 ─────────────────────────
@np.errstate(all="ignore")
def main():
    pad = bodies(load_stl(HW / "full/7_22 set_final.stl"))
    plate = [t for t in pad if size(t)[0] > 100]
    units = [t for t in pad if size(t)[0] < 100]
    assert len(plate) == 1 and len(units) == 24, (len(plate), len(units))
    ps = size(plate[0])
    total_h = size(np.concatenate(pad))[2]

    pin = bodies(load_stl(HW / "assembly/SG90 and Rack and Pinion.stl"))
    role = {}
    for t in pin:
        sx, sy, sz = size(t)
        if sz > 50:
            role["rack"] = t
        elif sx > 26 and sy > 26:
            role["servo"] = t
        elif abs(sx - sz) < 0.5 and sx < 20:
            role["pinion"] = t
        else:
            role["bracket"] = t
    assert len(pin) == 4 and len(role) == 4, [size(t).round(1) for t in pin]

    # (a) 촉각 패드 — 서보 쪽에서 본 모습
    pa = [(plate[0], PLATE)] + [(u, SERVO) for u in units]
    va = View(32, -58, 4.0, np.concatenate([t.reshape(-1, 3) for t, _ in pa]))
    ia = render(pa, va)
    # (b) 핀 구동부
    pb = [(role["servo"], SERVO), (role["bracket"], ORANGE), (role["pinion"], GREEN), (role["rack"], BLUE)]
    vb = View(22, -40, 10.0, np.concatenate([t.reshape(-1, 3) for t, _ in pb]))
    ib = render(pb, vb)

    fig = plt.figure(figsize=(COL_W, 1.68))
    ax = fig.add_axes([0.0, 0.0, 0.60, 0.88])
    ax.imshow(ia, interpolation="lanczos")
    ax.set_axis_off()
    ax2 = fig.add_axes([0.60, 0.0, 0.24, 0.88])
    ax2.imshow(ib, interpolation="lanczos")
    ax2.set_axis_off()

    fig.text(0.0, 0.99, "(a)", fontsize=7.5, fontweight="bold", va="top")
    fig.text(0.075, 0.99, f"촉각 패드  {ps[1]:.0f} × {ps[0]:.0f} × {total_h:.1f} mm", fontsize=6.2, va="top")
    fig.text(0.61, 0.99, "(b)", fontsize=7.5, fontweight="bold", va="top")
    fig.text(0.685, 0.99, "핀 구동부", fontsize=6.2, va="top")

    def note(axis, view, p3, text, xy_text, color, ha="left", relpos=(0, 0.5)):
        x, y = view.px(p3)[0]
        axis.annotate(text, xy=(x, y), xycoords="data", xytext=xy_text, textcoords="figure fraction",
                      fontsize=5.7, color=color, ha=ha, va="center", linespacing=1.1,
                      arrowprops=dict(arrowstyle="-", lw=0.45, color=color, shrinkA=1.5, shrinkB=0, relpos=relpos))

    def center(t):
        v = t.reshape(-1, 3)
        return (v.min(0) + v.max(0)) / 2

    def top(t):
        v = t.reshape(-1, 3)
        c = (v.min(0) + v.max(0)) / 2
        return np.array([c[0], c[1], v.max(0)[2]])

    # 그림 왼쪽 위 빈자리에서 가장 왼쪽 서보 유닛을, 오른쪽 아래 빈자리에서 베이스판 앞면을 가리킨다
    left = min(units, key=lambda t: va.px(top(t))[0, 0])
    note(ax, va, top(left), "서보 유닛 × 24\n(4행 × 6열)", (0.01, 0.70), SERVO, relpos=(0.3, 0))
    pv = plate[0].reshape(-1, 3)
    pf = np.array([pv[:, 0].max(), pv[:, 1].min() + 0.65 * (pv[:, 1].max() - pv[:, 1].min()), pv[:, 2].max() * 0.4])
    note(ax, va, pf, "베이스판", (0.47, 0.08), GRAY, relpos=(0.2, 1))

    rk = role["rack"].reshape(-1, 3)
    note(ax2, vb, np.array([rk[:, 0].mean(), rk[:, 1].mean(), rk[:, 2].max() - 4]), "랙(핀)", (0.865, 0.76), BLUE)
    note(ax2, vb, center(role["pinion"]), "피니언\n12잇수", (0.865, 0.52), GREEN)
    note(ax2, vb, center(role["servo"]), "SG90", (0.865, 0.30), SERVO)
    bv = role["bracket"].reshape(-1, 3)
    note(ax2, vb, np.array([bv[:, 0].mean(), bv[:, 1].mean(), bv[:, 2].min() + 2]), "브래킷", (0.865, 0.10), ORANGE)

    FIG.mkdir(parents=True, exist_ok=True)
    out = FIG / "fig_hw_cad.png"
    fig.savefig(out, facecolor="white", bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("저장:", out, "| 베이스판", np.round(ps, 2), "전체 높이", round(float(total_h), 2),
          "피니언 외경", round(float(size(role["pinion"])[0]), 2), "랙 길이", round(float(size(role["rack"])[2]), 2))


if __name__ == "__main__":
    main()
