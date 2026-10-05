#!/usr/bin/env python3
"""
논문 v3의 통계와 그림을 만든다.

  python analyze.py            data/*.csv → results.json, ../figures/v3/*.png

실험 1~3 CSV는 지금 예시 데이터다(example=1). 실측 CSV로 바꾸면 같은 명령으로 표·그림 값이 갱신된다.
그림 2, 3, 4(매핑 곡선·소프트웨어 처리 시간·처리 화면)는 실제 장치 코드와 실기 로그로 그린다.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
from scipy import stats  # noqa: E402

HERE = Path(__file__).resolve().parent
DATA = HERE / "data"
FIG = HERE.parent / "figures" / "v3"
DEV = Path.home() / "tactile-vision"
sys.path.insert(0, str(DEV / "src"))

for f in ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf"):
    font_manager.fontManager.addfont(f)
plt.rcParams.update({"font.family": "NanumGothic", "axes.unicode_minus": False, "font.size": 10,
                     "figure.dpi": 150, "savefig.dpi": 200, "savefig.bbox": "tight"})
R: dict = {}


def load(name: str) -> list[dict]:
    return list(csv.DictReader((DATA / name).open(encoding="utf-8")))


def d(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    return {"n": int(x.size), "mean": round(float(x.mean()), 2), "sd": round(float(x.std(ddof=1)), 2),
            "median": round(float(np.median(x)), 2), "min": round(float(x.min()), 2), "max": round(float(x.max()), 2),
            "p95": round(float(np.percentile(x, 95)), 2)}


# ─────────────────────────────────────────────────────────
# 실측: 소프트웨어 단계별 처리 시간 (2026-10-05 Pico 연결 실전 실행 2회)
# ─────────────────────────────────────────────────────────
def software_timing() -> None:
    rows = []
    for f in ("metrics_2026-10-05_1909_before_invert.csv", "metrics_2026-10-05_1925_inverted.csv"):
        rows += list(csv.DictReader((DEV / "logs" / f).open(encoding="utf-8")))
    col = lambda k: np.array([float(r[k]) for r in rows])  # noqa: E731
    sc = col("scene_ms")
    out = {k: d(col(f"{k}_ms")) for k in ("age", "depth", "hazard", "filter", "tx", "total")}
    out["scene_when_run"] = d(sc[sc > 2])
    out["scene_frame_share"] = round(float((sc > 2).mean()), 3)
    out["frames"] = len(rows)
    out["fps"] = round(1000 / float(col("total_ms").mean()), 1)
    R["software"] = out

    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.3), gridspec_kw={"width_ratios": [1.25, 1]})
    tot = col("total_ms")
    ax[0].hist(tot, bins=np.arange(40, 121, 2), color="#4a6fa5", edgecolor="white", linewidth=0.4)
    ax[0].axvline(np.median(tot), color="k", ls="--", lw=1)
    ax[0].text(np.median(tot) + 1.5, ax[0].get_ylim()[1] * 0.9, f"중앙값 {np.median(tot):.1f} ms", fontsize=9)
    ax[0].set_xlabel("프레임 처리 시간 (ms)")
    ax[0].set_ylabel("프레임 수")
    ax[0].set_title(f"(a) 프레임 처리 시간 분포 (n = {len(rows):,})", fontsize=10)
    names = ["깊이 추정", "위험 물체 검출", "장면 판별(판별 프레임)", "필터·매핑", "USB 전송"]
    means = [out["depth"]["mean"], out["hazard"]["mean"], out["scene_when_run"]["mean"], out["filter"]["mean"], out["tx"]["mean"]]
    p95 = [out["depth"]["p95"], out["hazard"]["p95"], out["scene_when_run"]["p95"], out["filter"]["p95"], out["tx"]["p95"]]
    y = np.arange(len(names))[::-1]
    ax[1].barh(y, means, color="#7a9cc6", label="평균")
    ax[1].errorbar(p95, y, fmt="|", color="k", ms=10, label="95 백분위")
    for yy, m, q in zip(y, means, p95):
        ax[1].text(max(m, q) + 1.2, yy, f"{m:.1f}", va="center", fontsize=8.5)
    ax[1].set_xlim(0, 62)
    ax[1].set_yticks(y, names)
    ax[1].set_xlabel("시간 (ms)")
    ax[1].set_title("(b) 단계별 처리 시간", fontsize=10)
    ax[1].legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "fig4-1_software_timing.png")
    plt.close(fig)


# ─────────────────────────────────────────────────────────
# 실측(코드): 거리 → 핀 단계 매핑
# ─────────────────────────────────────────────────────────
def mapping_curve() -> None:
    from tactile_vision.config import load as load_cfg
    from tactile_vision.mapping import DepthMapper

    cfg = load_cfg()
    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    ds = np.exp(np.linspace(np.log(0.3), np.log(10), 600))
    for far, lab, c in ((4.0, "실내 (d_far = 4 m)", "#c0504d"), (8.0, "실외 (d_far = 8 m)", "#4f81bd")):
        m = DepthMapper(cfg.mapping, cfg.filter, 1)
        m.set_far(far)
        cont = np.array([float(m._continuous(np.array([x]))[0]) for x in ds])
        lv = np.floor(cont + 0.5)
        ax.plot(ds, cont * cfg.mapping.stroke_mm / (cfg.mapping.levels - 1), color=c, lw=1, alpha=0.5)
        ax.step(ds, lv * cfg.mapping.stroke_mm / (cfg.mapping.levels - 1), where="mid", color=c, lw=1.8, label=lab)
    ax.set_xscale("log")
    ax.set_xticks([0.5, 1, 2, 4, 8], ["0.5", "1", "2", "4", "8"])
    ax.set_xlabel("칸 대표 거리 (m, 로그 눈금)")
    ax.set_ylabel("핀 돌출 높이 (mm)")
    ax2 = ax.twinx()
    ax2.set_ylim(np.array(ax.get_ylim()) / (cfg.mapping.stroke_mm / (cfg.mapping.levels - 1)))
    ax2.set_yticks(range(8))
    ax2.set_ylabel("단계")
    ax.grid(alpha=0.25, which="both")
    ax.legend(fontsize=9, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "fig3-3_mapping_curve.png")
    plt.close(fig)


# ─────────────────────────────────────────────────────────
# 그림: 시스템 구성도, 실험 3 코스
# ─────────────────────────────────────────────────────────
def block_diagram() -> None:
    fig, ax = plt.subplots(figsize=(10, 3.9))
    ax.set_xlim(0, 100)
    ax.set_ylim(-1.5, 40)
    ax.axis("off")

    def box(x, y, w, h, title, body, fc):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2", fc=fc, ec="#333", lw=0.9))
        ax.text(x + w / 2, y + h - 2.2, title, ha="center", va="top", fontsize=9.5, weight="bold")
        ax.text(x + w / 2, y + h - 6.2, body, ha="center", va="top", fontsize=7.8, linespacing=1.45)

    def arrow(x0, y0, x1, y1, lab="", lx=None, ly=None):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=11, lw=1.1, color="#333"))
        if lab:
            ax.text((x0 + x1) / 2 if lx is None else lx, (y0 + y1) / 2 + 1.6 if ly is None else ly, lab,
                    ha="center", fontsize=7.3, color="#333")

    ax.add_patch(Rectangle((14.5, -0.6), 49, 39.1, fc="none", ec="#888", ls="--", lw=0.8))
    ax.text(15.5, 1.1, "NVIDIA Jetson Orin Nano Super (25 W 모드)", fontsize=8, color="#555", va="center")
    box(0.5, 13, 11.5, 14, "카메라", "Logitech C920\n1280×720, 30 fps\nMJPG, 초점 고정", "#f2f2f2")
    box(16.5, 21, 14, 13, "장면 판별", "Places365\nResNet18\n초당 2회", "#e8eef7")
    box(16.5, 4, 14, 14, "입력 전처리", "중앙 크롭\n1280×698\n→ 924×504", "#f2f2f2")
    box(33, 21, 13.5, 13, "깊이 추정", "Depth Anything V2\nmetric ViT-S\n실내/실외 TRT", "#e8eef7")
    box(33, 4, 13.5, 14, "위험 물체", "YOLO26n\nTRT FP16\n512×288", "#e8eef7")
    box(49.5, 12.5, 12.5, 15, "매핑", "24칸 하위 10%\n로그 0.5~d_far\n비대칭 필터\n8단계", "#fdf0e0")
    box(67, 12.5, 13, 15, "제어부", "Raspberry Pi\nPico (RP2040)\n박자 200 ms\n슬루·failsafe", "#e9f3e6")
    box(84, 12.5, 15.5, 15, "촉각 패드", "PCA9685 ×2\nSG90 ×24\n랙·피니언 핀\n4×6, 9.0 mm", "#e9f3e6")
    arrow(12, 20, 16.5, 11, "USB", lx=12.6, ly=13.2)
    arrow(23.5, 18, 23.5, 21)
    arrow(30.5, 11, 33, 11)
    arrow(30.5, 31, 33, 31, "모델\n선택", lx=31.75, ly=34.6)
    arrow(30.5, 14, 33, 25)
    arrow(46.5, 27.5, 49.5, 23, "거리", lx=48.6, ly=29.2)
    arrow(46.5, 11, 49.5, 16, "위험 칸", lx=48.4, ly=8.0)
    arrow(62, 20, 67, 20, "USB\n31 B", lx=64.5, ly=22.2)
    arrow(80, 20, 84, 20, "I²C", lx=82, ly=22.0)
    fig.savefig(FIG / "fig3-1_system_block.png")
    plt.close(fig)


def course_diagram() -> None:
    fig, ax = plt.subplots(figsize=(9, 2.9))
    ax.set_xlim(-0.8, 11.2)
    ax.set_ylim(-0.4, 2.8)
    ax.set_aspect("equal")
    ax.add_patch(Rectangle((0, 0), 10.4, 2.4, fc="#fafafa", ec="#444", lw=1.5))
    ax.plot([0.2, 0.2], [0.2, 2.2], color="#2e7d32", lw=3)
    ax.plot([10.2, 10.2], [0.2, 2.2], color="#c62828", lw=3)
    ax.text(0.2, 2.55, "출발", ha="center", fontsize=9)
    ax.text(10.2, 2.55, "도착 (10 m)", ha="center", fontsize=9)
    obs = [(2.4, 0.55, 0.4, 0.4, "#8d6e63", "① 바닥 상자\n(높이 45 cm)"),
           (4.6, 1.45, 0.45, 0.3, "#5c6bc0", "② 사람 크기 판\n(170 cm)"),
           (6.8, 0.75, 0.5, 0.08, "#ef6c00", "③ 머리 높이 판\n(하단 145 cm)"),
           (8.6, 1.85, 0.45, 0.45, "#78909c", "④ 벽 쪽 의자")]
    for x, y, w, h, c, lab in obs:
        ax.add_patch(Rectangle((x, y), w, h, fc=c, ec="k", lw=0.6))
        ax.text(x + w / 2, y - 0.12, lab, ha="center", va="top", fontsize=7.2)
    for x in range(0, 11, 2):
        ax.text(x + 0.2, -0.3, f"{x} m", ha="center", fontsize=7, color="#666")
    ax.text(5.2, 2.35, "복도 폭 2.4 m · 배치 L1 예 (L2·L3는 ①~④의 위치·좌우를 바꿈)", ha="center", va="top", fontsize=7.5, color="#555")
    ax.axis("off")
    fig.savefig(FIG / "fig3-6_course.png")
    plt.close(fig)


def sample_frame() -> None:
    import cv2

    p = Path.home() / "Desktop" / "촉각비전_샘플영상" / "IMG_8423_촉각처리.mp4"
    if not p.exists():
        return
    cap = cv2.VideoCapture(str(p))
    cap.set(cv2.CAP_PROP_POS_FRAMES, 52)
    ok, f = cap.read()
    if ok:
        cv2.imwrite(str(FIG / "fig3-5_processing_view.jpg"), f, [cv2.IMWRITE_JPEG_QUALITY, 88])


# ─────────────────────────────────────────────────────────
# 실험 1
# ─────────────────────────────────────────────────────────
def exp1() -> None:
    rows = load("exp1_latency.csv")
    out = {"example": any(r["example"] == "1" for r in rows)}
    fig, ax = plt.subplots(1, 2, figsize=(9, 3.2), sharey=False)
    for i, (c, lab) in enumerate((("A_approach", "A. 접근 (핀 상승)"), ("B_recede", "B. 후퇴 (핀 하강)"))):
        on = np.array([float(r["onset_ms"]) for r in rows if r["cond"] == c])
        st = np.array([float(r["settle_ms"]) for r in rows if r["cond"] == c])
        sm = np.array([float(r["stroke_mm"]) for r in rows if r["cond"] == c])
        out[c] = {"onset": d(on), "settle": d(st), "stroke_mm": d(sm)}
        bp = ax[i].boxplot([on, st], widths=0.45, patch_artist=True, medianprops={"color": "k"})
        for b, fc in zip(bp["boxes"], ("#9db7d5", "#e6b88a")):
            b.set_facecolor(fc)
        jit = np.random.default_rng(1).uniform(-0.12, 0.12, on.size)
        ax[i].scatter(1 + jit, on, s=8, color="#2f4f7f", zorder=3)
        ax[i].scatter(2 + jit, st, s=8, color="#8a5a2b", zorder=3)
        ax[i].set_xticks([1, 2], ["움직임 시작", "목표 높이 도달"])
        ax[i].set_ylabel("사건 발생 후 시간 (ms)")
        ax[i].set_title(f"{lab}, n = {on.size}", fontsize=10)
        ax[i].grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG / "fig4-2_exp1_latency.png")
    plt.close(fig)
    R["exp1"] = out


# ─────────────────────────────────────────────────────────
# 실험 2
# ─────────────────────────────────────────────────────────
def exp2() -> None:
    rows = load("exp2_zero_offset.csv")
    out = {"example": any(r["example"] == "1" for r in rows)}
    per = {}
    for ph in ("before", "after"):
        z = np.array([[float(r["zero_mm"]) for r in rows if r["phase"] == ph and int(r["pin"]) == p] for p in range(24)])
        t = np.array([[float(r["top_mm"]) for r in rows if r["phase"] == ph and int(r["pin"]) == p] for p in range(24)])
        m = z.mean(1)
        per[ph] = m
        out[ph] = {"pin_mean": d(m), "abs_dev": d(np.abs(m)),
                   "within_sd_pooled": round(float(np.sqrt(z.var(1, ddof=1).mean())), 3),
                   "within_sd_max": round(float(z.std(1, ddof=1).max()), 3),
                   "stroke": d((t - z).mean(1)),
                   "worst_pin": int(np.argmax(np.abs(m))),
                   "n_over_1step": int(np.sum(np.abs(m) > 9.0 / 7))}
    w = stats.wilcoxon(np.abs(per["before"]), np.abs(per["after"]))
    out["wilcoxon_abs"] = {"W": float(w.statistic), "p": float(w.pvalue)}
    lev = stats.levene(per["before"], per["after"])
    out["levene"] = {"F": round(float(lev.statistic), 2), "p": float(lev.pvalue)}
    R["exp2"] = out

    fig, ax = plt.subplots(1, 2, figsize=(9.5, 3.3), gridspec_kw={"width_ratios": [1.6, 1]})
    x = np.arange(24)
    ax[0].bar(x - 0.2, per["before"], 0.4, color="#c9a27e", label="보정 전")
    ax[0].bar(x + 0.2, per["after"], 0.4, color="#5b8bb8", label="채널별 보정 후")
    ax[0].axhline(0, color="k", lw=0.8)
    ax[0].axhspan(-9.0 / 7 / 2, 9.0 / 7 / 2, color="#999", alpha=0.12, label="±0.5단계 (±0.64 mm)")
    ax[0].set_xticks(x, [str(i) for i in x], fontsize=7)
    ax[0].set_xlabel("핀 번호 (칸 순서, 1행 왼쪽 → 4행 오른쪽)")
    ax[0].set_ylabel("레벨 0 핀 끝 높이 (mm)")
    ax[0].legend(fontsize=8, ncol=3, loc="upper right")
    ax[0].set_title("(a) 핀별 영점 높이 (10회 평균)", fontsize=10)
    for k, (ph, lab) in enumerate((("before", "보정 전"), ("after", "보정 후"))):
        g = per[ph].reshape(4, 6)
        im = ax[1].imshow(g, cmap="RdBu_r", vmin=-2, vmax=2, extent=(k * 6.6, k * 6.6 + 6, 4, 0))
        for r_ in range(4):
            for c_ in range(6):
                ax[1].text(k * 6.6 + c_ + 0.5, r_ + 0.5, f"{g[r_, c_]:.1f}", ha="center", va="center", fontsize=6.5)
        ax[1].text(k * 6.6 + 3, -0.35, lab, ha="center", fontsize=9)
    ax[1].set_xlim(0, 12.6)
    ax[1].set_ylim(4, -0.8)
    ax[1].axis("off")
    ax[1].set_title("(b) 패드 위 배치 (mm)", fontsize=10)
    fig.colorbar(im, ax=ax[1], fraction=0.04, pad=0.02)
    fig.tight_layout()
    fig.savefig(FIG / "fig4-3_exp2_zero_offset.png")
    plt.close(fig)


# ─────────────────────────────────────────────────────────
# 실험 3
# ─────────────────────────────────────────────────────────
def exp3() -> None:
    rows = load("exp3_walking.csv")
    out = {"example": any(r["example"] == "1" for r in rows)}
    conds = ["cane", "device", "cane_device"]
    ps = sorted({r["participant"] for r in rows}, key=lambda s: int(s[1:]))
    kinds = ["low", "panel", "head", "side", "wall"]
    T = np.array([[np.mean([float(r["time_s"]) for r in rows if r["participant"] == p and r["cond"] == c]) for c in conds] for p in ps])
    C = np.array([[np.mean([sum(int(r[f"col_{k}"]) for k in kinds) for r in rows if r["participant"] == p and r["cond"] == c]) for c in conds] for p in ps])
    base = np.array([float(next(r["baseline_s"] for r in rows if r["participant"] == p)) for p in ps])
    S = (10.0 / T) / (10.0 / base[:, None]) * 100   # 평소 걷는 속도 대비 %
    out["baseline_s"] = d(base)
    for j, c in enumerate(conds):
        tri = [float(r["time_s"]) for r in rows if r["cond"] == c]
        out[c] = {"time_participant": d(T[:, j]), "collisions_per_trial": d(C[:, j]), "speed_pct": d(S[:, j]),
                  "time_trial": d(tri),
                  "by_kind": {k: round(float(np.mean([int(r[f"col_{k}"]) for r in rows if r["cond"] == c])), 2) for k in kinds},
                  "zero_collision_trials": int(sum(sum(int(r[f"col_{k}"]) for k in kinds) == 0 for r in rows if r["cond"] == c)),
                  "trial_means": [round(float(np.mean([float(r["time_s"]) for r in rows if r["cond"] == c and int(r["trial"]) == k])), 1) for k in (1, 2, 3)]}
    fr_t = stats.friedmanchisquare(*T.T)
    fr_c = stats.friedmanchisquare(*C.T)
    out["friedman_time"] = {"chi2": round(float(fr_t.statistic), 2), "p": float(fr_t.pvalue)}
    out["friedman_col"] = {"chi2": round(float(fr_c.statistic), 2), "p": float(fr_c.pvalue)}
    post = {}
    for a, b in ((0, 1), (0, 2), (1, 2)):
        for name, M in (("time", T), ("col", C)):
            try:
                w = stats.wilcoxon(M[:, a], M[:, b])
                p = min(1.0, float(w.pvalue) * 3)
                post[f"{name}_{conds[a]}_vs_{conds[b]}"] = {"W": float(w.statistic), "p_bonf": round(p, 4)}
            except ValueError:
                post[f"{name}_{conds[a]}_vs_{conds[b]}"] = {"W": None, "p_bonf": 1.0}
    out["posthoc"] = post
    dev_t = [[float(r["time_s"]) for r in rows if r["participant"] == p and r["cond"] == "device" and int(r["trial"]) == k][0] for p in ps for k in (1, 3)]
    dev_t = np.array(dev_t).reshape(len(ps), 2)
    w = stats.wilcoxon(dev_t[:, 0], dev_t[:, 1])
    out["device_learning"] = {"trial1": d(dev_t[:, 0]), "trial3": d(dev_t[:, 1]), "W": float(w.statistic), "p": float(w.pvalue)}
    out["per_participant"] = {"time": T.round(1).tolist(), "col": C.round(2).tolist(), "speed": S.round(0).tolist(), "baseline": base.tolist()}
    R["exp3"] = out

    labs = ["흰지팡이", "본 장치", "흰지팡이 + 본 장치"]
    cols = ["#9e9e9e", "#5b8bb8", "#6aa56a"]
    fig, ax = plt.subplots(1, 3, figsize=(10.5, 3.3))
    for k, (M, yl, tt) in enumerate(((T, "완주 시간 (s)", "(a) 10 m 완주 시간"), (C, "시행당 충돌 (회)", "(b) 충돌 횟수"))):
        for j in range(3):
            ax[k].bar(j, M[:, j].mean(), 0.6, yerr=M[:, j].std(ddof=1), color=cols[j], capsize=3, alpha=0.85)
        for i in range(len(ps)):
            ax[k].plot(range(3), M[i], color="#444", lw=0.6, alpha=0.5, marker="o", ms=2.5)
        ax[k].set_xticks(range(3), labs, fontsize=8)
        ax[k].set_ylabel(yl)
        ax[k].set_title(tt, fontsize=10)
        ax[k].grid(axis="y", alpha=0.25)
    kl = {"low": "바닥 상자", "panel": "사람 크기 판", "head": "머리 높이 판", "side": "벽 쪽 의자", "wall": "벽 접촉"}
    bottom = np.zeros(3)
    kc = ["#8d6e63", "#5c6bc0", "#ef6c00", "#78909c", "#bdbdbd"]
    for k, cc in zip(kinds, kc):
        v = np.array([out[c]["by_kind"][k] for c in conds])
        ax[2].bar(range(3), v, 0.6, bottom=bottom, color=cc, label=kl[k])
        bottom += v
    ax[2].set_xticks(range(3), labs, fontsize=8)
    ax[2].set_ylabel("시행당 충돌 (회)")
    ax[2].set_title("(c) 충돌 대상별", fontsize=10)
    ax[2].legend(fontsize=7, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "fig4-4_exp3_walking.png")
    plt.close(fig)


if __name__ == "__main__":
    FIG.mkdir(parents=True, exist_ok=True)
    software_timing()
    mapping_curve()
    block_diagram()
    course_diagram()
    sample_frame()
    exp1()
    exp2()
    exp3()
    (HERE / "results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(R, ensure_ascii=False, indent=1))
