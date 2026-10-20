"""D판(새 설계판) 그림과 계산 값 (2026-10-19, iMac).

이미 측정·분석한 출력 파일만 읽는다. 새 측정은 없다.
입력 (모두 thesis/analysis/ 아래)
  - out_distance/ground/ground_rows.csv : 사진 120장, 방법별 추정 거리 (ground_scale.py 출력)
  - out_distance/ground/summary.json    : 땅 기준 환산 민감도 (ground_scale.py 출력)
  - out_latency/trials.csv              : 구동 지연 20회 중 ok == 1인 17회 (latency_flip.py 출력)
  - out_level/summary.json              : 처리 시간 7,894프레임 통계 등 (level_budget.py 출력)
  - out_pin_zero/cells.csv              : 24칸 영점 보정량 (pin_zero.py 출력)
출력
  - thesis/figures/kiro_D/fig_D_system.png, fig_D_ground.png, fig_D_mapping.png,
    fig_D_distance.png, fig_D_timing.png  (가로 2.9 inch, 300 dpi, 한 단 폭)
  - thesis/analysis/out_kiro_D/derived.md, derived.json  (원고에 쓰는 계산 값과 입력 파일)

실행: /Users/skku_aws3_08/Documents/p1/.venv/bin/python kiro_D_figures.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures" / "kiro_D"
OUT = HERE / "out_kiro_D"

GROUND_ROWS = HERE / "out_distance/ground/ground_rows.csv"
GROUND_SUMMARY = HERE / "out_distance/ground/summary.json"
TRIALS = HERE / "out_latency/trials.csv"
LEVEL_SUMMARY = HERE / "out_level/summary.json"
PIN_CELLS = HERE / "out_pin_zero/cells.csv"

D_NEAR = 0.5
D_FAR = {"indoor": 8.0, "outdoor": 20.0}  # 장치 ground-scale 가지 설정 (실내 8 m, 실외 20 m)
LEVELS = 8
MM_PER_TICK = 0.0646
MM_PER_LEVEL = 20 * MM_PER_TICK  # 1.292 mm
WIDTH_IN = 2.9  # 한 단(7.46 cm) 안

C_IN, C_IN_RAW = "#2a78d6", "#7aa6d9"
C_OUT, C_OUT_RAW = "#1b9e77", "#e0702e"
C_GRAY = "#555555"


def setup() -> None:
    plt.rcParams.update({
        # Apple SD Gothic Neo에 없는 글자(− 등)는 DejaVu Sans로 채운다(matplotlib 3.6 이상 글자별 대체)
        "font.family": ["Apple SD Gothic Neo", "DejaVu Sans"],
        "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7,
        "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6,
        "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "lines.linewidth": 1.0, "figure.dpi": 300, "savefig.dpi": 300,
        "savefig.facecolor": "white", "axes.unicode_minus": True, "mathtext.fontset": "dejavusans",
    })


# ───────────────────────── 매핑 식 (장치와 같음) ─────────────────────────
def level_cont(d, d_far):
    """반올림 전 표시 단계. level_budget.py·calib_compare.py와 같은 식(로그 차의 비, 0.5 m~d_far로 자름)."""
    d = np.clip(np.asarray(d, dtype=float), D_NEAR, d_far)
    return (math.log(d_far) - np.log(d)) / (math.log(d_far) - math.log(D_NEAR)) * (LEVELS - 1)


def level_int(d, d_far):
    return np.rint(level_cont(d, d_far)).astype(int)


def first_level_distance(d_far: float) -> float:
    """핀이 처음 올라오는(반올림해 1단계가 되는) 거리 = 연속 단계 0.5인 거리."""
    return d_far * (D_NEAR / d_far) ** (0.5 / (LEVELS - 1))


# ───────────────────────── 자료 읽기 ─────────────────────────
def load_ground() -> pd.DataFrame:
    g = pd.read_csv(GROUND_ROWS)
    ind = g[g["env"] == "indoor"]
    # 장소 교차 더하기 보정: 다른 장소 실내 사진의 평균(실제 − 추정)을 더한다 (level_budget.py metric_cross와 같음)
    b = {s: float((ind.loc[ind.site == s, "true_m"] - ind.loc[ind.site == s, "metric"]).mean()) for s in ("site1", "site2")}
    other = {"site1": "site2", "site2": "site1"}
    g["metric_cross"] = np.where(g["env"] == "indoor", g["metric"] + g["site"].map(lambda s: b[other[s]]), np.nan)
    g.attrs["b_site"] = b
    return g


def cross_k(g: pd.DataFrame, env: str, model: str) -> dict:
    """× k 장소 교차(calib_compare.py와 같은 식: k = Σ(t·e)/Σ(e²), 다른 장소에 적용, 0.05 m 아래로 자르기)."""
    far = D_FAR[env]
    e_all = g[g["env"] == env]
    ape, ok, pm1, dl = [], [], [], []
    for a, b in (("site1", "site2"), ("site2", "site1")):
        ta, ea = e_all.loc[e_all.site == a, "true_m"].to_numpy(), e_all.loc[e_all.site == a, model].to_numpy()
        tb, eb = e_all.loc[e_all.site == b, "true_m"].to_numpy(), e_all.loc[e_all.site == b, model].to_numpy()
        k = float(np.sum(ta * ea) / np.sum(ea * ea))
        pb = np.maximum(k * eb, 0.05)
        ape += list(np.abs(pb - tb) / tb * 100)
        d = level_int(pb, far) - level_int(tb, far)
        ok += list(d == 0)
        pm1 += list(np.abs(d) <= 1)
        dl += list(np.abs(level_cont(pb, far) - level_cont(tb, far)))
    return {"mape": float(np.mean(ape)), "level_match": float(np.mean(ok) * 100),
            "level_within1": float(np.mean(pm1) * 100), "dlevel_mean": float(np.mean(dl))}


# ───────────────────────── [그림 1] 구성도 ─────────────────────────
def box(ax, x, y, w, h, text, fc="white", ec="#333333", lw=0.7, ls="-", fs=6.5, weight="normal", r=1.2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                fc=fc, ec=ec, lw=lw, ls=ls, zorder=2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, weight=weight,
            linespacing=1.25, zorder=3)


def arrow(ax, x, y0, y1, label=None, dx=1.5):
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="-|>", lw=0.7, color="#333333", mutation_scale=6), zorder=1)
    if label:
        ax.text(x + dx, (y0 + y1) / 2, label, ha="left", va="center", fontsize=5.8, color="#333333")


def fig_system() -> Path:
    fig = plt.figure(figsize=(WIDTH_IN, 3.5))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 121)
    ax.axis("off")
    X, W = 2, 64  # 본체 상자 열
    box(ax, X, 110.5, W, 9.5, "카메라 Logitech C920\n1280×720, 렌즈 높이 0.70 m, 수평")
    arrow(ax, X + W / 2, 110.5, 106.6)
    # Jetson 묶음
    ax.add_patch(FancyBboxPatch((X - 1, 47.5), W + 2, 58.8, boxstyle="round,pad=0,rounding_size=1.5",
                                fc="#f3f6fa", ec="#2a5d9f", lw=0.8, zorder=0))
    # 깊이·YOLO는 TensorRT FP16, Places365는 PyTorch FP16이라 묶음 이름에 TensorRT를 쓰지 않는다(2회차 수정)
    ax.text(X + 0.8, 103.6, "Jetson Orin Nano (25 W 모드)", ha="left", va="center", fontsize=6.2,
            weight="bold", color="#2a5d9f")
    box(ax, X + 2, 92.5, W - 4, 8.4, "장면 판별: Places365 ResNet18, 초당 2회\n실외 ≥ 0.65 / 실내 ≤ 0.35, 1.5 s 유지 후 전환",
        fs=6.0)
    arrow(ax, X + W * 0.27, 92.5, 89.4)
    arrow(ax, X + W * 0.73, 92.5, 89.4)
    box(ax, X + 2, 77.5, W / 2 - 3, 11.6, "실내\n미터 깊이\n− 0.44 m", fc="#e9f1fb", fs=6.0)
    box(ax, X + W / 2 + 1, 77.5, W / 2 - 3, 11.6, "실외\n상대 깊이 →\n땅 기준 환산", fc="#e8f5f0", fs=6.0)
    arrow(ax, X + W * 0.27, 77.5, 74.4)
    arrow(ax, X + W * 0.73, 77.5, 74.4)
    box(ax, X + 2, 66.6, W - 4, 7.4, "칸 값: 6 × 4칸, 칸마다 거리의 하위 10%", fs=6.0)
    arrow(ax, X + W / 2, 66.6, 63.4)
    box(ax, X + 2, 55.0, W - 4, 8.0, "표시 단계 0~7 (로그 눈금, 0.5 m ~ $d_{\\mathrm{far}}$)\n$d_{\\mathrm{far}}$: 실내 8 m, 실외 20 m", fs=6.0)
    box(ax, X + 2, 49.2, W - 4, 4.8, "보조: YOLO26n 위험 물체 → 핀 1~3° 진동(평가 안 함)",
        ec="#888888", ls="--", fs=5.5)
    arrow(ax, X + W / 2, 47.5, 40.4, label="USB, 31바이트 프레임\n(CRC-8), 약 15 Hz", dx=1.2)
    box(ax, X, 26.6, W, 13.6, "Pico 호환 RP2040 보드\n0.2 s 박자마다 받은 값 중 최신 값을 목표로\n속도 제한 4 tick / 5 ms\n끊김 0.5 s → 천천히 맨 아래", fs=6.0)
    arrow(ax, X + W / 2, 26.6, 23.2, label="I²C", dx=1.2)
    box(ax, X, 13.0, W, 10.0, "PCA9685 × 2 → SG90 × 24\n랙·피니언 핀 (행정 9.0 mm, 1단계 1.29 mm)", fs=6.0)
    arrow(ax, X + W / 2, 13.0, 10.0)
    box(ax, X, 1.2, W, 8.6, "양손 손바닥 (4행 × 6열)\n왼쪽 3열 = 왼손, 오른쪽 3열 = 오른손", fs=6.0)

    # 측정 위치 ①~④ (오른쪽 열)
    xb, xl = 70.0, 72.2
    col = "#c0392b"

    def bracket(y_top, y_bot):
        ax.plot([xb - 1.4, xb, xb, xb - 1.4], [y_top, y_top, y_bot, y_bot], color=col, lw=0.8, zorder=4)

    bracket(115.0, 44.0)
    ax.text(xl, 101, "① 처리 시간\n(프레임 대기\n + 처리)", ha="left", va="center", fontsize=6.1, color=col,
            linespacing=1.2)
    # ②는 실내·실외 깊이를 모두 쟀으므로 두 상자를 함께 점선으로 묶는다(2회차 수정)
    ax.add_patch(Rectangle((X + 1.0, 76.7), W - 2.0, 13.3, fill=False, ec=col, lw=0.6, ls=":", zorder=4))
    ax.plot([X + W - 1.0, xb], [83.3, 83.3], color=col, lw=0.6, ls=":", zorder=4)
    ax.text(xl, 83.3, "② 거리 정확도\n(사진 120장)", ha="left", va="center", fontsize=6.1, color=col, linespacing=1.2)
    bracket(43.0, 14.0)
    ax.text(xl, 34, "③ 구동 지연\n(전송 → 핀)", ha="left", va="center", fontsize=6.1, color=col, linespacing=1.2)
    ax.plot([X + W, xb + 3.0], [18.3, 18.3], color=col, lw=0.6, ls=":", zorder=4)
    ax.text(xl + 3.4, 18.3, "④ 핀 영점\n(24칸)", ha="left", va="center", fontsize=6.1, color=col, linespacing=1.2)
    p = FIG / "fig_D_system.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ───────────────────────── [그림 3] 땅 기준 환산 원리 ─────────────────────────
def fig_ground() -> Path:
    h, d_bot, d_top = 0.70, 1.82, 3.5
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 1.68))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    ax.set_xlim(-0.5, 5.6)
    ax.set_ylim(-0.84, 0.95)
    ax.axis("off")
    ax.plot([-0.45, 5.5], [0, 0], color="#333333", lw=0.9)
    ax.add_patch(Rectangle((d_bot, -0.06), d_top - d_bot, 0.06, fc=C_OUT, ec="none", alpha=0.75))
    ax.text((d_bot + d_top) / 2, -0.10, f"땅으로 보는 줄 ({d_bot:.2f}~{d_top:g} m 앞)", ha="center", va="top",
            fontsize=5.9, color=C_OUT)
    ax.add_patch(Rectangle((-0.16, h - 0.06), 0.2, 0.12, fc="#333333", ec="none"))
    ax.text(0.10, h + 0.07, "카메라", ha="left", va="bottom", fontsize=5.8)
    ax.plot([0.04, 5.4], [h, h], color=C_GRAY, lw=0.6, ls="--")
    ax.text(5.4, h + 0.04, "광축(수평)", ha="right", va="bottom", fontsize=5.6, color=C_GRAY)
    for d in (d_bot, d_top):
        ax.plot([0.04, d], [h, 0], color="#2a5d9f", lw=0.7)
    ax.text(1.22, 0.13, "화면 맨 아래 줄", ha="right", va="center", fontsize=5.5, color="#2a5d9f")
    ax.annotate("", xy=(-0.33, 0), xytext=(-0.33, h), arrowprops=dict(arrowstyle="<->", lw=0.6, color="#333333",
                                                                      mutation_scale=5))
    ax.text(-0.29, h * 0.62, "h\n0.70 m", ha="left", va="center", fontsize=5.8, linespacing=1.1)
    ax.add_patch(Rectangle((4.45, 0), 0.32, 0.30, fc="white", ec="#333333", lw=0.7))
    ax.text(4.61, 0.35, "물체", ha="center", va="bottom", fontsize=5.8)
    ax.text(-0.42, -0.33,
            "① 줄 y에 보이는 땅까지의 거리:  $d(y) = f\\,h\\,/\\,(y - y_0)$\n"
            "② 배율 A = 중앙값[ (줄의 r 중앙값) × $d(y)$ ]\n"
            "③ 각 화소의 거리 = A / r   (r: 상대 깊이, 클수록 가까움)",
            ha="left", va="top", fontsize=5.9, linespacing=1.5)
    ax.text(5.5, 0.93, "가로·세로 축척 다름", ha="right", va="top", fontsize=5.0, color=C_GRAY)
    p = FIG / "fig_D_ground.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ───────────────────────── [그림 4] 거리 → 표시 단계 ─────────────────────────
def fig_mapping() -> Path:
    fig, ax = plt.subplots(figsize=(WIDTH_IN, 2.0))
    fig.subplots_adjust(left=0.13, right=0.86, top=0.97, bottom=0.17)
    d = np.logspace(np.log10(0.3), np.log10(30), 2000)
    for env, col, lab in (("indoor", C_IN, "실내 ($d_{\\mathrm{far}}$ 8 m)"), ("outdoor", C_OUT, "실외 ($d_{\\mathrm{far}}$ 20 m)")):
        lv = np.floor(level_cont(d, D_FAR[env]) + 0.5)
        ax.step(d, lv, where="post", color=col, lw=1.1, label=lab)
        d1 = first_level_distance(D_FAR[env])
        ax.axvline(d1, color=col, lw=0.6, ls=":", ymax=0.80)
        ax.text(d1 * 1.04, 2.35 if env == "indoor" else 3.25, f"1단계 시작\n{d1:.2f} m" if env == "indoor" else f"1단계 시작\n{d1:.1f} m",
                fontsize=5.6, color=col, ha="left", va="bottom", linespacing=1.15)
    # 검증한 거리 범위
    ax.plot([0.5, 4], [8.05, 8.05], color=C_IN, lw=2.6, solid_capstyle="butt", alpha=0.55)
    ax.text(4.3, 8.05, "실내 검증 0.5~4 m", fontsize=5.6, color=C_IN, va="center")
    ax.plot([1, 8], [7.55, 7.55], color=C_OUT, lw=2.6, solid_capstyle="butt", alpha=0.55)
    ax.text(8.6, 7.55, "실외 검증 1~8 m", fontsize=5.6, color=C_OUT, va="center")
    ax.set_xscale("log")
    ax.set_xlim(0.3, 30)
    ax.set_ylim(-0.3, 8.5)
    ticks = [0.3, 0.5, 1, 2, 4, 8, 20]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{t:g}" for t in ticks])
    ax.minorticks_off()
    ax.set_yticks(range(8))
    ax.set_xlabel("거리 (m)")
    ax.set_ylabel("표시 단계")
    sec = ax.secondary_yaxis("right", functions=(lambda l: l * MM_PER_LEVEL, lambda mm: mm / MM_PER_LEVEL))
    sec.set_yticks([0, 3, 6, 9])
    sec.set_ylabel("핀 높이 (mm)")
    ax.legend(loc="lower left", frameon=False, handlelength=1.6, borderaxespad=0.3)
    for s in ("top",):
        ax.spines[s].set_visible(False)
    p = FIG / "fig_D_mapping.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ───────────────────────── [그림 5] 거리 정확도 ─────────────────────────
def fig_distance(g: pd.DataFrame) -> Path:
    fig, axes = plt.subplots(2, 1, figsize=(WIDTH_IN, 4.1))
    fig.subplots_adjust(left=0.14, right=0.97, top=0.985, bottom=0.08, hspace=0.31)
    panels = {
        "indoor": dict(ax=axes[0], title="(a) 실내 사진 ($d_{\\mathrm{far}}$ 8 m)", xlim=(0.42, 5.0), ylim=(0.3, 6.5),
                       xt=[0.5, 1, 1.5, 2, 3, 4], yt=[0.5, 1, 2, 4],
                       series=(("metric", "실내 모델 그대로", C_IN_RAW, "--", False),
                               ("metric_cross", "+ b (장소 교차)", C_IN, "-", True)),
                       sites={"site1": "거실", "site2": "주방"}, shared=True),
        "outdoor": dict(ax=axes[1], title="(b) 실외 사진 ($d_{\\mathrm{far}}$ 20 m)", xlim=(0.85, 9.5), ylim=(0.7, 150),
                        xt=[1, 2, 3, 4, 6, 8], yt=[1, 2, 4, 8, 16, 32, 64],
                        series=(("vkitti", "실외 모델 그대로", C_OUT_RAW, "--", False),
                                ("ground", "땅 기준 환산", C_OUT, "-", True)),
                        sites={"site1": "산책로", "site2": "주차장"}, shared=False),
    }
    for env, P in panels.items():
        ax = P["ax"]
        ratio = (D_FAR[env] / D_NEAR) ** (1 / (LEVELS - 1))
        xx = np.logspace(np.log10(P["xlim"][0]), np.log10(P["xlim"][1]), 50)
        ax.fill_between(xx, xx / ratio, xx * ratio, color="#d9d9d9", lw=0, zorder=0)
        ax.plot(xx, xx, color=C_GRAY, lw=0.7, ls=":", zorder=1)
        e = g[g["env"] == env]
        for k, lab, col, ls, filled in P["series"]:
            for site, mk, off in (("site1", "o", 0.965), ("site2", "s", 1.035)):
                s = e[e["site"] == site]
                ds = sorted(s["true_m"].unique())
                m = [s.loc[s.true_m == d, k].mean() for d in ds]
                sd = [s.loc[s.true_m == d, k].std(ddof=1) for d in ds]
                ax.errorbar(np.array(ds) * off, m, yerr=sd, color=col, ls=ls, lw=0.9, marker=mk, ms=3.0,
                            mfc=col if filled else "white", mec=col, mew=0.8, capsize=1.5, elinewidth=0.6, zorder=3)
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlim(*P["xlim"])
        ax.set_ylim(*P["ylim"])
        ax.set_xticks(P["xt"])
        ax.set_xticklabels([f"{t:g}" for t in P["xt"]])
        ax.set_yticks(P["yt"])
        ax.set_yticklabels([f"{t:g}" for t in P["yt"]])
        ax.minorticks_off()
        ax.set_xlabel("줄자 거리 (m)", labelpad=1.5)
        ax.set_ylabel("추정 거리 (m)", labelpad=1.5)
        ax.text(0.02, 0.97, P["title"], transform=ax.transAxes, ha="left", va="top", fontsize=7, weight="bold")
        hs = [Line2D([], [], color=col, ls=ls, lw=0.9, marker="o", ms=3.0, mfc=col if f else "white", mec=col,
                     label=lab) for _, lab, col, ls, f in P["series"]]
        hs += [Line2D([], [], color="#333333", ls="none", marker=mk, ms=3.0, mfc="white", mec="#333333", label=lab)
               for mk, lab in zip(("o", "s"), P["sites"].values())]
        if P["shared"]:  # 두 칸에 같은 뜻 — 위 칸에만 적는다
            hs += [Rectangle((0, 0), 1, 1, fc="#d9d9d9", ec="none", label="±1단계 범위(반올림 전)"),
                   Line2D([], [], color=C_GRAY, ls=":", lw=0.7, label="y = x")]
        ax.legend(handles=hs, loc="upper left", bbox_to_anchor=(0.0, 0.90), frameon=False, fontsize=5.6,
                  handlelength=1.8, labelspacing=0.25, borderaxespad=0.2)
    p = FIG / "fig_D_distance.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ───────────────────────── [그림 6] 반응 시간 ─────────────────────────
def fig_timing(trials: pd.DataFrame, proc: dict) -> Path:
    age = round(proc["age_ms"]["mean"], 1)
    tot = round(proc["total_ms"]["mean"], 1)
    wp = proc["wait_plus_total_ms"]
    onset = round(trials["onset_send_ms"].mean(), 1)
    move = round(trials["move_ms"].mean(), 1)
    fig = plt.figure(figsize=(WIDTH_IN, 2.95))
    ax1 = fig.add_axes([0.05, 0.775, 0.90, 0.10])
    ax2 = fig.add_axes([0.13, 0.12, 0.84, 0.46])
    # (a) 평균 구성 막대
    parts = [(age, "프레임 대기", "#bdbdbd"), (tot, "처리", C_IN), (onset, "박자 대기·서보 반응", "#f0b27a"),
             (move, "이동(5→95%)", C_OUT_RAW)]
    left = 0.0
    for i, (v, lab, col) in enumerate(parts):
        ax1.barh(0, v, left=left, color=col, height=0.8, ec="white", lw=0.6)
        ax1.text(left + v / 2, 0, f"{v:.1f}", ha="center", va="center", fontsize=5.8,
                 color="white" if i in (1, 3) else "#222222")
        ax1.text(left + v / 2, 0.75 if i % 2 == 0 else -0.75, lab, ha="center", va="bottom" if i % 2 == 0 else "top",
                 fontsize=5.6)
        left += v
    total = round(age + tot + onset + move, 1)
    ax1.set_xlim(0, 400)
    ax1.set_ylim(-0.5, 0.5)
    ax1.axis("off")
    fig.text(0.05, 0.975, f"(a) 평균 구성 (ms): 처리(대기 포함) {age + tot:.1f} + 구동 {onset + move:.1f} = {total:.1f}",
             ha="left", va="top", fontsize=6.6, weight="bold")
    # (b) 17회 시행
    t = trials.sort_values("arrive_send_ms").reset_index(drop=True)
    y = np.arange(1, len(t) + 1)
    for col_name, mk, col, lab in (("onset_send_ms", "o", C_IN, "시작"), ("arrive_send_ms", "s", C_OUT_RAW, "도착")):
        lo = t[col_name] + wp["mean"]
        hi = t[col_name] + wp["max"]
        ax2.hlines(y, lo, hi, color=col, lw=0.7, alpha=0.8)
        ax2.plot(lo, y, ls="none", marker=mk, ms=2.8, color=col, label=f"{lab} (+ 처리 평균 {wp['mean']:.1f} ms)")
        ax2.plot(hi, y, ls="none", marker="|", ms=4.0, mew=0.9, color=col)
    ax2.plot([], [], ls="none", marker="|", ms=4.0, mew=0.9, color="#333333", label=f"+ 처리 최댓값 {wp['max']:.1f} ms")
    for xv, lab in ((500, "시작 기준 0.5 s"), (1000, "도착 기준 1 s")):
        ax2.axvline(xv, color=C_GRAY, lw=0.7, ls="--")
        ax2.text(xv, 1.015, lab, transform=ax2.get_xaxis_transform(), ha="center" if xv == 500 else "right",
                 va="bottom", fontsize=5.6, color=C_GRAY)
    ax2.set_xlim(0, 1050)
    ax2.set_ylim(0.2, len(t) + 0.8)
    ax2.set_yticks([1, 5, 10, 15, 17])
    ax2.set_xlabel("처리 시간 + 구동 지연 합산 (ms)")
    ax2.set_ylabel("시행 (도착 순)")
    ax2.legend(loc="lower right", frameon=False, fontsize=5.6, handlelength=1.2, labelspacing=0.25, borderaxespad=0.2)
    fig.text(0.05, 0.695, "(b) 시행별 시작·도착 (17회)", ha="left", va="top", fontsize=6.6, weight="bold")
    p = FIG / "fig_D_timing.png"
    fig.savefig(p)
    plt.close(fig)
    return p


# ───────────────────────── 계산 값 기록 ─────────────────────────
def derived(g: pd.DataFrame, trials: pd.DataFrame, lev: dict, gsum: dict, cells: pd.DataFrame) -> dict:
    proc = lev["processing"]
    lat = lev["latency"]
    r1 = lambda x: round(float(x), 1)  # noqa: E731
    age, tot, wp = r1(proc["age_ms"]["mean"]), r1(proc["total_ms"]["mean"]), r1(proc["wait_plus_total_ms"]["mean"])
    onset, move, arrive = r1(trials["onset_send_ms"].mean()), r1(trials["move_ms"].mean()), r1(trials["arrive_send_ms"].mean())
    total = r1(wp + arrive)
    D = {}
    D["timing"] = {
        "src": [str(LEVEL_SUMMARY.relative_to(HERE)), str(TRIALS.relative_to(HERE)) + " (ok == 1)"],
        "age_plus_total": f"{age} + {tot} = {r1(age + tot)} (프레임별 합의 평균 {wp})",
        "onset_plus_move": f"{onset} + {move} = {r1(onset + move)} (도착 평균 {arrive})",
        "proc_plus_drive": f"{wp} + {arrive} = {total}",
        "start_total": f"{wp} + {onset} = {r1(wp + onset)}",
        "share_proc_pct": round(wp / total * 100, 1), "share_drive_pct": round(arrive / total * 100, 1),
        "onset_range_width_ms": r1(trials["onset_send_ms"].max() - trials["onset_send_ms"].min()),
        "onset_minus_beat_ms": r1(lat["onset_minus_beat_mean_ms"]),
        "slew_full_stroke_ms": 140 / 4 * 5, "slew_5to95_ms": lat["slew_model_move_ms"],
        "walk_m_arrive_mean": round(lat["walk_m_at_arrive_mean"], 2),
        "walk_m_arrive_max_p95": round(lat["walk_m_at_arrive_max_p95"], 2),
        "fps_display_on": round(2 / proc["scene_run_frac"], 2),
        "scene_p95_ms": r1(proc["scene_ms_run"]["p95"]),
        "n_trials": int(len(trials)), "n_up": int((trials["dir"] == "up").sum()), "n_down": int((trials["dir"] == "down").sum()),
    }
    D["mapping"] = {
        "src": "식만 사용 (level_budget.py와 같은 매핑)",
        "first_level_m": {k: round(first_level_distance(v), 2) for k, v in D_FAR.items()},
        "ratio_per_level": {k: round((v / D_NEAR) ** (1 / (LEVELS - 1)), 3) for k, v in D_FAR.items()},
        "stroke_mm": round(140 * MM_PER_TICK, 2), "mm_per_level": round(MM_PER_LEVEL, 3),
        "step_5tick_mm": round(5 * MM_PER_TICK, 3), "step_5tick_level": 5 / 20,
        "pinion_tooth_mm": round(math.pi * 16.00 / 12, 2), "pinion_tooth_tick": round(math.pi * 16.00 / 12 / MM_PER_TICK, 1),
    }
    # 실내 바닥이 1.82 m → 약 1.4 m로 계산될 때 단계 차 (실내 d_far 8 m, 반올림 전)
    D["mapping"]["floor_1p82_vs_1p4_level"] = round(float(level_cont(1.4, 8.0) - level_cont(1.82, 8.0)), 2)
    D["mapping"]["floor_levels_rounded"] = [int(level_int(1.82, 8.0)), int(level_int(1.4, 8.0))]
    # 카메라 기하 (f 908 px, 1280×720에서 가운데 698줄 사용, h 0.70 m)
    half_rows = 698 / 2
    f_px, h = 908.0, 0.70
    D["geometry"] = {
        "src": "가정값 h 0.70 m, f 908 px, 가운데 1280×698 (ground_scale.py·relative_depth.py와 같음)",
        "bottom_row_ground_m": round(f_px * h / half_rows, 2),
        "half_vfov_deg": round(math.degrees(math.atan(half_rows / f_px)), 1),
        "visible_height_at_1m_m": round(h - 1.0 * half_rows / f_px, 3),
        "theory_ratio_vkitti": round((1.65 / 0.70) * (725 / 375) / (908 / 698), 2),
    }
    # 거리: 장소별 b, 실내 모델의 거리별 더함 오차, × k 장소 교차(|Δ| 포함)
    b = g.attrs["b_site"]
    ind = g[g["env"] == "indoor"]
    off = {float(d): round(float((ind.loc[ind.true_m == d, "metric"] - d).mean()), 2) for d in sorted(ind.true_m.unique())}
    D["distance"] = {
        "src": str(GROUND_ROWS.relative_to(HERE)),
        "b_site_m": {k: round(v, 2) for k, v in b.items()},
        "indoor_metric_offset_by_distance_m": off,
        "indoor_metric_offset_range_m": [min(off.values()), max(off.values())],
        "xk_cross_indoor": {k: round(v, 2) for k, v in cross_k(g, "indoor", "metric").items()},
        "xk_cross_outdoor": {k: round(v, 2) for k, v in cross_k(g, "outdoor", "vkitti").items()},
        "check_against": "out_distance/calib_compare.md: 실내 × k 18.0 / 70 / 98, 실외 × k 63.2 / 25 / 80",
    }
    sens = gsum["sensitivity"]
    # 원고에 적은(소수 한 자리로 반올림한) MAPE끼리의 차. 반올림 전 값끼리의 차는 괄호 안.
    rs = lambda grp, key: r1(sens[grp][key]["mape"])  # noqa: E731
    base = rs("tilt_deg", "0")
    raw = lambda grp, key: r1(sens[grp][key]["mape"] - sens["tilt_deg"]["0"]["mape"])  # noqa: E731
    D["sensitivity"] = {
        "src": str(GROUND_SUMMARY.relative_to(HERE)) + " sensitivity",
        "base_mape": base,
        "tilt_minus1_delta_pp": [r1(rs("tilt_deg", "-1") - base), raw("tilt_deg", "-1")],
        "tilt_plus1_delta_pp": [r1(rs("tilt_deg", "1") - base), raw("tilt_deg", "1")],
        "height_0p65_delta_pp": [r1(rs("height_m", "0.65") - base), raw("height_m", "0.65")],
        "height_0p75_delta_pp": [r1(rs("height_m", "0.75") - base), raw("height_m", "0.75")],
    }
    e = cells["err_mm"].to_numpy(float)
    s = cells["shift_tick"].to_numpy(int)
    D["pin_zero"] = {
        "src": str(PIN_CELLS.relative_to(HERE)),
        "n_zero": int((s == 0).sum()), "n_pos": int((s > 0).sum()), "n_neg": int((s < 0).sum()),
        "n_le1": int((np.abs(s) <= 20).sum()), "n_gt1": int((np.abs(s) > 20).sum()), "n_gt2": int((np.abs(s) > 40).sum()),
        "abs_mean_level": round(float(np.abs(e).mean() / MM_PER_LEVEL), 2), "max_level": float(np.abs(s).max() / 20),
        "col4_mm": [float(x) for x in cells.loc[cells.col == 4, "err_mm"]],
    }
    D["gait_ref"] = {"src": "Bohannon 1997 초록 127.2~146.2 cm/s", "m_per_s": [1.27, 1.46]}
    return D


def write_derived(D: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "derived.json").write_text(json.dumps(D, ensure_ascii=False, indent=1), encoding="utf-8")
    t, m, gm, d, sn, pz = D["timing"], D["mapping"], D["geometry"], D["distance"], D["sensitivity"], D["pin_zero"]
    L = ["# D판 계산 값 (자동 생성: kiro_D_figures.py)", "",
         "이미 있는 출력 파일만 읽어 계산하였다. 새 측정은 없다. 각 줄 끝 괄호는 입력 파일(thesis/analysis/ 기준).", "",
         "## 반응 시간 구성", f"입력: {', '.join(t['src'])}",
         f"- 프레임 대기 + 처리: {t['age_plus_total']}",
         f"- 전송→시작 + 이동: {t['onset_plus_move']}",
         f"- 장면 변화 → 시작(평균 합): {t['start_total']} ms",
         f"- 장면 변화 → 도착(평균 합): {t['proc_plus_drive']} ms",
         f"- 비율: 처리 {t['share_proc_pct']}%, 구동 {t['share_drive_pct']}% (반올림 27% / 73%)",
         f"- 시작 시간 범위 폭: {t['onset_range_width_ms']} ms; 시작 평균 − 박자 대기 기대값 100 ms = {t['onset_minus_beat_ms']} ms",
         f"- 속도 제한 계산: 끝→끝 {t['slew_full_stroke_ms']:.0f} ms, 5→95% {t['slew_5to95_ms']} ms",
         f"- 1.2 m/s 보행 거리: 도착 평균 {t['walk_m_arrive_mean']} m, p95 합산 최대 {t['walk_m_arrive_max_p95']} m",
         f"- 확인 화면을 켠 실행의 실제 갱신: 2회/s ÷ 판별 실행 비율 = {t['fps_display_on']} fps",
         f"- 장면 판별 시간 p95(실행 프레임): {t['scene_p95_ms']} ms",
         f"- 시행 수: {t['n_trials']} (올림 {t['n_up']}, 내림 {t['n_down']})", "",
         "## 매핑·기구", f"입력: {m['src']}",
         f"- 1단계 시작 거리: 실내 {m['first_level_m']['indoor']} m, 실외 {m['first_level_m']['outdoor']} m",
         f"- 이웃 단계 거리 비: 실내 {m['ratio_per_level']['indoor']}, 실외 {m['ratio_per_level']['outdoor']}",
         f"- 행정 140 tick × 0.0646 = {m['stroke_mm']} mm, 1단계 20 tick = {m['mm_per_level']} mm, "
         f"조정 걸음 5 tick = {m['step_5tick_mm']} mm = {m['step_5tick_level']}단계",
         f"- 피니언 이 하나(π × 16.00 / 12) = {m['pinion_tooth_mm']} mm = {m['pinion_tooth_tick']} tick",
         f"- 실내 바닥 1.82 m → 1.4 m일 때 단계 차(반올림 전, d_far 8 m): {m['floor_1p82_vs_1p4_level']}단계 "
         f"(반올림 단계 {m['floor_levels_rounded'][0]} → {m['floor_levels_rounded'][1]})", "",
         "## 카메라 기하", f"입력: {gm['src']}",
         f"- 맨 아래 줄의 땅: {gm['bottom_row_ground_m']} m 앞, 세로 반화각 {gm['half_vfov_deg']}°, "
         f"1 m 앞에서 보이는 가장 낮은 높이 {gm['visible_height_at_1m_m']} m",
         f"- 실외 모델 이론 배율 (1.65/0.70)×(725/375)/(908/698) = {gm['theory_ratio_vkitti']:.2f} "
         "(학습 카메라 높이 1.65 m·초점 725 px·세로 375 px는 가정값)", "",
         "## 거리", f"입력: {d['src']}",
         f"- 장소별 더하기 보정 b(실제 − 추정 평균): 거실 {d['b_site_m']['site1']} m, 주방 {d['b_site_m']['site2']} m",
         f"- 실내 모델 거리별 (추정 − 실제) 평균: {d['indoor_metric_offset_by_distance_m']} → 범위 "
         f"{d['indoor_metric_offset_range_m'][0]} ~ {d['indoor_metric_offset_range_m'][1]} m",
         f"- × k 장소 교차, 실내: {d['xk_cross_indoor']}",
         f"- × k 장소 교차, 실외: {d['xk_cross_outdoor']}",
         f"- 대조: {d['check_against']}", "",
         f"## 민감도 (실외 MAPE, 기준 {sn['base_mape']}%에서의 변화 %p; 반올림한 값끼리의 차 [반올림 전 값끼리의 차])",
         f"입력: {sn['src']}",
         f"- 기울기 −1° / +1°: {sn['tilt_minus1_delta_pp'][0]} [{sn['tilt_minus1_delta_pp'][1]}] / "
         f"{sn['tilt_plus1_delta_pp'][0]} [{sn['tilt_plus1_delta_pp'][1]}]",
         f"- 가정 높이 0.65 / 0.75 m: {sn['height_0p65_delta_pp'][0]} [{sn['height_0p65_delta_pp'][1]}] / "
         f"{sn['height_0p75_delta_pp'][0]} [{sn['height_0p75_delta_pp'][1]}]",
         "- 원고 표현: '기울기 1°나 높이 5 cm가 틀리면 MAPE가 약 4~6%p 바뀐다'", "",
         "## 핀 영점", f"입력: {pz['src']}",
         f"- 0칸 {pz['n_zero']}, 튀어나옴 {pz['n_pos']}, 들어감 {pz['n_neg']}, ≤ 1단계 {pz['n_le1']}, > 1단계 {pz['n_gt1']}, "
         f"> 2단계 {pz['n_gt2']}, 절댓값 평균 {pz['abs_mean_level']}단계, 최대 {pz['max_level']}단계",
         f"- 4열 네 칸(mm): {pz['col4_mm']}", "",
         "## 보행 속도 참고", f"- {D['gait_ref']['src']} → {D['gait_ref']['m_per_s'][0]}~{D['gait_ref']['m_per_s'][1]} m/s", ""]
    (OUT / "derived.md").write_text("\n".join(L), encoding="utf-8")


def main() -> int:
    setup()
    FIG.mkdir(parents=True, exist_ok=True)
    g = load_ground()
    trials = pd.read_csv(TRIALS)
    trials = trials[trials["ok"] == 1].copy()
    lev = json.loads(LEVEL_SUMMARY.read_text(encoding="utf-8"))
    gsum = json.loads(GROUND_SUMMARY.read_text(encoding="utf-8"))
    cells = pd.read_csv(PIN_CELLS)
    made = [fig_system(), fig_ground(), fig_mapping(), fig_distance(g), fig_timing(trials, lev["processing"])]
    D = derived(g, trials, lev, gsum, cells)
    write_derived(D)
    for p in made:
        print("그림:", p)
    print("계산:", OUT / "derived.md")
    print((OUT / "derived.md").read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
