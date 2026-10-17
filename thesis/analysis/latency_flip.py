"""핀 구동 지연 — 화면 흰·검 전환과 칸 9 핀을 폰 슬로모션으로 함께 찍은 영상 분석.

장치 쪽: ~/tactile-vision-ground/tools/servo_latency_flip.py (2026-10-17, 녹화 3회 × 전환 20번)
  젯슨이 깊이 계산 없이 칸 9를 0 ↔ 7단계로 바꿔 보내고, 보낸 바로 뒤 창을 흰색(올림)·검은색(내림)으로 바꾼다.
  평소처럼 초당 15번 계속 보내고, Pico(펌웨어 v3)는 0.2 s 박자마다 최신 값만 적용한다.
영상: Galaxy S10 5G 슬로모션. 파일 시간표는 30 fps지만 실제로는 약 240 fps → 실효 fps는 로그로 맞춘다.
  1·2회는 손에 들고 찍어 구도가 움직였다(2회는 중간에 확대). 고정해서 찍은 3회만 쓴다.

방법
  1. 영상을 처음부터 차례로 읽는다(이 파일은 프레임 탐색이 15프레임 이상 어긋난다).
     프레임마다 화면 영역 밝기와 핀 주변 회색조 조각을 모은다 → 캐시
  2. 화면 밝기가 흰·검 중간값을 지나는 순간(앞뒤 프레임 선형 보간) = 전환이 보인 순간
  3. 로그 t_shown과 짝지어 실효 fps(기울기)를 구한다. 잔차로 프레임 누락 여부를 본다
  4. 핀 추적: 전환 40프레임 전의 핀 윗부분(구멍 윗끝 포함)을 템플릿으로, 이동 방향 쪽으로만 정규화 상관 탐색.
     옆의 고정 구조(서보 몸체)도 같이 추적해 흔들림을 뺀다
  5. 진행률 p = (y − 처음)/(끝 − 처음). 시작 = p가 5%를 넘는 순간, 도착 = 95%를 넘는 순간(보간)
  6. 전송 기준 = 영상 기준 + show_ms(로그: 전송 → 화면 갱신 명령 반환).
     모니터가 실제로 그리기까지의 지연은 재지 못했으므로 전송 기준 값은 그만큼 짧게(하한) 나온다

  python latency_flip.py              # 캐시가 없으면 영상을 한 번 읽는다(약 5분)
"""
from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RAW = HERE / "data" / "raw" / "latency_flip_20261017"
OUT = HERE / "out_latency"
VID_DIR = Path.home() / "Videos" / "latency_flip_1017"  # 영상 원본(저장소 밖, 약 1.9 GB)
CACHE = VID_DIR / "cache"

# 상자 좌표는 영상 원본 픽셀(1080×1920). crop 안의 pin/ref는 crop 기준 (y0, y1, x0, x1)
RUNS = {
    3: dict(video="20261017_210259.mp4", log="latency_flip_1017_2103.csv",
            screen=(40, 280, 80, 1000), crop=(880, 1180, 520, 720),
            pin=(128, 162, 74, 120), ref=(250, 290, 10, 60)),
}
PRE = 40        # 템플릿·시작 위치를 잡는 프레임 (전환 전)
POST = 260      # 전환 뒤 추적 길이
FINAL = (170, 250)  # 끝 위치를 잡는 구간 (전환 뒤 프레임)
P_ON, P_ARR = 0.05, 0.95
TRAVEL_PX = (38.0, 50.0)  # 정상 이동량 범위 (9.0 mm ≈ 43.5 px)
SHAKE_PX = 1.0  # 고정 구조가 이보다 많이 움직인 전환(폰이 흔들림)은 뺀다


def scan(run: int) -> dict:
    path = CACHE / f"run{run}_scan.npz"
    if path.exists():
        d = np.load(path)
        return {"scr": d["scr"], "crop": d["crop"]}
    import cv2

    cfg = RUNS[run]
    sy0, sy1, sx0, sx1 = cfg["screen"]
    cy0, cy1, cx0, cx1 = cfg["crop"]
    cap = cv2.VideoCapture(str(VID_DIR / cfg["video"]))
    scr, crop = [], []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        scr.append(float(f[sy0:sy1:4, sx0:sx1:4].mean()))
        crop.append(cv2.cvtColor(f[cy0:cy1, cx0:cx1], cv2.COLOR_BGR2GRAY))
    CACHE.mkdir(parents=True, exist_ok=True)
    out = {"scr": np.array(scr, np.float32), "crop": np.array(crop)}
    np.savez(path, **out)
    return out


def load_log(name: str) -> list[dict]:
    with open(RAW / name, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(line for line in fh if not line.startswith("#"))]
    return [{"n": int(r["n"]), "dir": r["dir"], "t_send": float(r["t_send_s"]),
             "t_shown": float(r["t_shown_s"]), "show_ms": float(r["show_ms"])} for r in rows]


def flips(scr: np.ndarray) -> list[tuple[float, int, str]]:
    """(보간한 전환 시각[프레임], 넘어선 첫 프레임, up/down)."""
    lo, hi = np.percentile(scr, 5), np.percentile(scr, 95)
    mid = (lo + hi) / 2
    w = scr > mid
    out = []
    for f in np.flatnonzero(np.diff(w.astype(int)) != 0) + 1:
        a, b = float(scr[f - 1]), float(scr[f])
        out.append((f - 1 + (mid - a) / (b - a), int(f), "up" if w[f] else "down"))
    return out


def pair(fl: list, log: list[dict]) -> tuple[int, float, float, np.ndarray]:
    """방향이 맞는 연속 구간 중 로그 t_shown과 직선이 가장 잘 맞는 시작 위치 → (시작, fps, 절편, 잔차 ms)."""
    n = len(log)
    best = None
    for s in range(len(fl) - n + 1):
        if any(fl[s + i][2] != log[i]["dir"] for i in range(n)):
            continue
        x = np.array([r["t_shown"] for r in log])
        y = np.array([fl[s + i][0] for i in range(n)])
        k, b = np.polyfit(x, y, 1)
        res = (y - (k * x + b)) / k * 1000
        if best is None or np.abs(res).max() < np.abs(best[3]).max():
            best = (s, float(k), float(b), res)
    if best is None:
        raise SystemExit("로그와 방향이 맞는 전환 구간이 없음")
    return best


def match(g: np.ndarray, tpl: np.ndarray, y: int, x: int, dy: tuple[int, int], sx: int = 8):
    """템플릿을 (y, x) 기준 세로 dy[0]~dy[1], 가로 ±sx에서 찾는다 → (세로 이동 소수, 가로 이동, 상관)."""
    import cv2

    h, w = tpl.shape
    y0, x0 = max(y + dy[0], 0), max(x - sx, 0)
    win = g[y0:y + h + dy[1], x0:x + w + sx].astype(np.float32)
    r = cv2.matchTemplate(win, tpl.astype(np.float32), cv2.TM_CCOEFF_NORMED)
    _, mv, _, (mx, my) = cv2.minMaxLoc(r)
    fy = float(my)
    if 0 < my < r.shape[0] - 1:
        a, b, c = r[my - 1, mx], r[my, mx], r[my + 1, mx]
        den = a - 2 * b + c
        if den != 0:
            fy = my + 0.5 * (a - c) / den
    return y0 + fy - y, x0 + mx - x, float(mv)


def cross(t: np.ndarray, p: np.ndarray, level: float, start: int) -> float:
    """start부터 p가 level을 넘고 다음 2프레임도 넘는 첫 지점(앞 프레임과 선형 보간)."""
    for j in range(max(start, 1), len(p) - 2):
        if p[j] >= level and p[j + 1] >= level and p[j + 2] >= level:
            return float(t[j - 1] + (level - p[j - 1]) / (p[j] - p[j - 1]) * (t[j] - t[j - 1]))
    return math.nan


def track(G: np.ndarray, F: int, d: str, cfg: dict, base: np.ndarray) -> dict:
    """전환 한 번의 핀 진행률. F = 화면이 바뀐 첫 프레임."""
    py0, py1, px0, px1 = cfg["pin"]
    ry0, ry1, rx0, rx1 = cfg["ref"]
    a = F - PRE
    # 시작 위치: 핀이 아래(올림 전)면 기준 상자 근처, 위(내림 전)면 그보다 25~60 px 위
    rng = (-8, 8) if d == "up" else (-60, -25)
    dy, dx, _ = match(G[a], base, py0, px0, rng)
    y0, x0 = int(round(py0 + dy)), int(px0 + dx)
    tpl = G[a][y0:y0 + py1 - py0, x0:x0 + px1 - px0]
    rtpl = G[a][ry0:ry1, rx0:rx1]
    way = (-60, 6) if d == "up" else (-6, 60)
    fr = np.arange(a, min(F + POST, len(G)))
    disp, corr, rdy, rdx = [], [], [], []
    for j in fr:
        p = match(G[j], tpl, y0, x0, way)
        r = match(G[j], rtpl, ry0, rx0, (-15, 15))
        disp.append(p[0] - r[0])
        corr.append(p[2])
        rdy.append(r[0])
        rdx.append(r[1])
    disp, corr = np.array(disp), np.array(corr)
    rel = fr - F
    init = float(np.median(disp[(rel >= -PRE) & (rel < -20)]))
    fin = float(np.median(disp[(rel >= FINAL[0]) & (rel < FINAL[1])]))
    p = (disp - init) / (fin - init)
    shake = max(float(np.ptp(rdy)), float(np.ptp(rdx)))
    return {"rel": rel, "p": p, "travel_px": abs(fin - init), "min_corr": float(corr.min()),
            "shake_px": shake}


def analyse(run: int) -> tuple[list[dict], dict]:
    cfg = RUNS[run]
    S = scan(run)
    G = S["crop"]
    log = load_log(cfg["log"])
    fl = flips(S["scr"])
    s, fps, b, res = pair(fl, log)
    py0, py1, px0, px1 = cfg["pin"]
    first_up = next(f for f in fl[s:] if f[2] == "up")
    base = G[first_up[1] - PRE][py0:py1, px0:px1]
    rows = []
    for i, lg in enumerate(log):
        tf, F, d = fl[s + i]
        tr = track(G, F, d, cfg, base)
        t = tr["rel"] + (F - tf)  # 보인 전환 시각 기준 프레임(소수)
        on = cross(t, tr["p"], P_ON, 10)
        start = int(np.searchsorted(t, on)) if math.isfinite(on) else 10
        arr = cross(t, tr["p"], P_ARR, start)
        ms = 1000.0 / fps
        ok = (TRAVEL_PX[0] <= tr["travel_px"] <= TRAVEL_PX[1] and tr["shake_px"] <= SHAKE_PX
              and math.isfinite(on) and math.isfinite(arr))
        rows.append({"run": run, "n": lg["n"], "dir": d, "flip_frame": round(tf, 2),
                     "fit_resid_ms": round(float(res[i]), 2), "show_ms": lg["show_ms"],
                     "onset_video_ms": round(on * ms, 1), "arrive_video_ms": round(arr * ms, 1),
                     "onset_send_ms": round(on * ms + lg["show_ms"], 1),
                     "arrive_send_ms": round(arr * ms + lg["show_ms"], 1),
                     "move_ms": round((arr - on) * ms, 1), "travel_px": round(tr["travel_px"], 1),
                     "min_corr": round(tr["min_corr"], 3), "shake_px": round(tr["shake_px"], 1), "ok": int(ok), "_t": t * ms, "_p": tr["p"]})
    info = {"run": run, "fps": fps, "flips_found": len(fl), "paired_from": s,
            "resid_ms_max": float(np.abs(res).max()), "resid_ms_sd": float(res.std(ddof=1)),
            "frames": int(len(S["scr"]))}
    return rows, info


def describe(v: list[float]) -> dict:
    a = np.array(v, float)
    return {"n": len(a), "mean": a.mean(), "sd": a.std(ddof=1), "median": float(np.median(a)),
            "min": a.min(), "max": a.max(), "p95": float(np.percentile(a, 95))}


def fmt(d: dict) -> str:
    return (f"n {d['n']}, 평균 {d['mean']:.1f} ms (SD {d['sd']:.1f}), 중앙값 {d['median']:.1f}, "
            f"범위 {d['min']:.1f}~{d['max']:.1f}, p95 {d['p95']:.1f}")


def figure(rows: list[dict]) -> None:
    from distance_analysis import setup_mpl

    plt = setup_mpl()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=True)
    for ax, d, title in zip(axes, ("up", "down"), ("(a) 올림 (0 → 7단계)", "(b) 내림 (7 → 0단계)")):
        for r in rows:
            if r["dir"] != d or not r["ok"]:
                continue
            ax.plot(r["_t"] + r["show_ms"], r["_p"] * 100, color="#2a78d6", lw=1.0, alpha=0.55)
            ax.plot([r["onset_send_ms"]], [P_ON * 100], "o", ms=3.5, color="#1b5e9e")
            ax.plot([r["arrive_send_ms"]], [P_ARR * 100], "s", ms=3.5, color="#c4572b")
        ax.axvline(0, color="#555555", lw=0.8, ls="--")
        ax.set_xlim(-60, 600)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("전송 뒤 시간 (ms)")
    axes[0].set_ylabel("핀 이동 진행률 (%)")
    axes[0].plot([], [], "o", color="#1b5e9e", label="시작 (5%)")
    axes[0].plot([], [], "s", color="#c4572b", label="도착 (95%)")
    axes[0].legend(loc="lower right", fontsize=8, frameon=False)
    fig.savefig(OUT / "fig_latency_flip.png")
    plt.close(fig)


def sheet(run: int, rows: list[dict]) -> None:
    """확인용: 전환마다 [전환 전, 시작, 도착] 핀 조각을 한 줄로."""
    import cv2

    G = scan(run)["crop"]
    lines = []
    for r in rows:
        F = int(math.ceil(r["flip_frame"]))
        cells = []
        for lab, ms in (("before", -100.0), ("onset", r["onset_video_ms"]), ("arrive", r["arrive_video_ms"])):
            j = F + int(round(ms / 1000.0 * r["_fps"])) if math.isfinite(ms) else F
            im = cv2.cvtColor(G[min(max(j, 0), len(G) - 1)][60:220, 40:160], cv2.COLOR_GRAY2BGR)
            cv2.putText(im, f"{r['n']}{r['dir'][0]} {lab}", (2, 12), 0, 0.38, (0, 0, 255), 1)
            cells.append(im)
        lines.append(np.hstack(cells))
    half = (len(lines) + 1) // 2
    left, right = lines[:half], lines[half:]
    while len(right) < len(left):
        right.append(np.zeros_like(left[0]))
    cv2.imwrite(str(OUT / f"sheet_run{run}.jpg"), np.hstack([np.vstack(left), np.vstack(right)]))


def main() -> int:
    OUT.mkdir(exist_ok=True)
    runs = [int(a) for a in sys.argv[1:]] or sorted(RUNS)
    rows, infos = [], []
    for run in runs:
        rr, info = analyse(run)
        for r in rr:
            r["_fps"] = info["fps"]
        rows += rr
        infos.append(info)
        sheet(run, rr)
    keys = [k for k in rows[0] if not k.startswith("_")]
    with open(OUT / "trials.csv", "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, keys)
        wr.writeheader()
        for r in rows:
            wr.writerow({k: r[k] for k in keys})
    good = [r for r in rows if r["ok"]]
    lines = ["# 핀 구동 지연 (화면 전환 방식, 2026-10-17)", "",
             "`python latency_flip.py` 출력. 시작 = 이동 5%, 도착 = 95%. 전송 기준 = 영상 기준 + show_ms "
             "(모니터 표시 지연 미포함 → 하한).", ""]
    for info in infos:
        lines.append(f"- 녹화 {info['run']}: 프레임 {info['frames']}, 실효 {info['fps']:.2f} fps "
                     f"(로그 맞춤 잔차 최대 {info['resid_ms_max']:.1f} ms, SD {info['resid_ms_sd']:.1f} ms), "
                     f"전환 검출 {info['flips_found']}개 중 {info['paired_from'] + 1}번째부터 로그와 짝")
    bad = ", ".join(f"{r['run']}-{r['n']}{r['dir'][0]}(이동 {r['travel_px']} px, 흔들림 {r['shake_px']} px)"
                    for r in rows if not r["ok"])
    lines.append(f"- 쓴 전환 {len(good)}/{len(rows)}. 제외: {bad or '없음'} — 이동량 {TRAVEL_PX[0]:.0f}~{TRAVEL_PX[1]:.0f} px 밖, "
                 f"고정 구조가 {SHAKE_PX:.0f} px 넘게 움직임(폰 흔들림), 시작·도착 못 찾음")
    lines.append("")
    summ = {}
    for d, lab in (("all", "전체"), ("up", "올림"), ("down", "내림")):
        g = [r for r in good if d == "all" or r["dir"] == d]
        if not g:
            continue
        lines.append(f"## {lab}")
        for key, name in (("onset_send_ms", "전송 → 시작"), ("arrive_send_ms", "전송 → 도착"),
                          ("move_ms", "이동 시간(시작 → 도착)"), ("onset_video_ms", "화면 → 시작"),
                          ("arrive_video_ms", "화면 → 도착"), ("show_ms", "show_ms")):
            st = describe([r[key] for r in g])
            summ[f"{d}|{key}"] = {k: round(float(v), 2) for k, v in st.items()}
            lines.append(f"- {name}: {fmt(st)}")
        lines.append("")
    (OUT / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps({"runs": infos, "stats": summ}, ensure_ascii=False, indent=1),
                                      encoding="utf-8")
    figure(rows)
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
