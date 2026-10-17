# IR 발표 자료(영어) 갱신 지시 — 2026-10-17 실측 반영

> **이 파일은 비공개 저장소 전용이다.** 이 파일의 내용(지시문, 저장소 이름·경로, 아래 '넣지 말 것' 목록)은
> 발표 자료, 공개 저장소, 공개 커밋 메시지 어디에도 옮기지 않는다.

## 0. 사용자가 발표 자료 작업 세션에 붙여 넣을 한 줄

```
github.com/MuakTiger/tactile-vision-thesis 의 main을 pull해서 IR_DECK_TASK.md 를 읽고, 그 지시대로 기존 IR 발표 자료(영어)를 고쳐 줘.
```

---

## 1. 할 일

- **새로 만들지 말고 기존 IR 발표 자료(영어)를 고친다.** 구성·디자인은 그대로 두고, 수치와 기술 설명만 아래 실측 결과로 바꾼다.
- 바꾼 슬라이드마다 어떤 수치를 무엇으로 바꿨는지, 그 근거(FACTS 절 번호)를 작업이 끝난 뒤 사용자에게 목록으로 보고한다.
- 판단이 필요한 것(링크를 넣을지, 수치를 얼마나 자세히 쓸지)은 고치기 전에 사용자에게 묻는다.

## 2. 읽을 것 (이 저장소, 순서대로)

1. `HANDOFF.md` 맨 위 "2026-10-17 젯슨 세션 1~4" 절 — 오늘 바뀐 것 요약
2. `FACTS.md` §1.8~§1.11 — 수치 원장(거리 정확도, 땅 기준 환산, 반응 시간, 핀 영점). 처리 시간·전력은 §1.6(f)와 §1.10
3. `thesis/졸업논문_양식1.md` — 현재 논문 원고: 2.2 장치 구성·[표 1], Ⅲ 결과 3.1~3.4·[표 2~5]
4. 결과 요약과 그림
   - `thesis/analysis/out_distance/ground/summary.md`, `thesis/analysis/out_distance/calib_compare.md`
   - `thesis/analysis/out_latency/summary.md`, `thesis/analysis/out_pin_zero/summary.md`
   - 그림(그래프만, 사진 아님): `thesis/analysis/out_distance/ground/fig_thesis_distance.png`, `thesis/analysis/out_latency/fig_latency_flip.png`

## 3. 핵심 수치 (실측, 슬라이드용 영어 표현 예)

| 항목 | 값 | 영어 표현 예 | 근거 |
|---|---|---|---|
| 실외 거리 오차 | 땅 기준 환산 MAPE 21.1% vs 기존 실외 모델 518.5% (사진 60장, 2곳) | Outdoor distance error 21.1% (MAPE) with camera-height ground-plane scaling, vs 518% for an off-the-shelf outdoor metric model | FACTS §1.9 |
| 실내 거리 오차 | 실내 모델 − 0.44 m 보정, 장소 교차 MAPE 9.5% (사진 60장, 2곳) | Indoor distance error 9.5% (MAPE, cross-site) after a single offset correction | FACTS §1.8·§1.9 |
| 표시 단계 | 실내·실외 모두 실제와 ±1단계 이내 100% | Displayed pin level within ±1 of ground truth in 100% of photos | 원고 [표 3] |
| 처리 | Jetson Orin Nano 프레임당 68.8 ms, 초당 15.3프레임, 14.4 W | 68.8 ms per frame on Jetson Orin Nano (15.3 fps, 14.4 W) | FACTS §1.10, 원고 3.1 |
| 구동 지연 | 지령 → 핀 시작 평균 116 ms, 9 mm 도착 평균 280 ms(최대 379 ms), 17회 | Command-to-pin: motion starts in 116 ms and the full 9 mm stroke completes in 280 ms on average (max 379 ms, n = 17) | FACTS §1.10, 원고 3.3 |
| 반응 시간 합 | 처리 시간을 더한 도착 평균 약 384 ms. 17회 모두 시작 0.5 s·도착 1 s 기준 만족 (카메라 내부·모니터 지연 제외) | Frame-in to pin-set ≈ 0.38 s on average; all trials met the 0.5 s onset / 1 s arrival targets (camera-internal latency excluded) | 원고 3.3 |
| 핀 영점 | 조립 영점 오차 SD 2.20 mm(범위 −3.55 ~ +5.17 mm, 최대 4단계) → 핀별 소프트웨어 보정을 펌웨어에 넣음 | Per-pin software zero calibration corrects assembly offsets (SD 2.2 mm, up to 4 display levels), stored in firmware | FACTS §1.11, 원고 3.4 |
| 표시 범위 | 0.5 m ~ 실내 8 m / 실외 20 m, 로그 눈금 8단계, 핀 0~9.0 mm | 8 log-scaled levels over 0.5–8 m indoors / 0.5–20 m outdoors, 0–9 mm pin height | 원고 [표 1] |

## 4. 바꿔야 할 옛 값 (발표 자료에 있으면 고칠 것)

- `thesis/졸업논문_v3.md`의 실험 1~3 수치와 `thesis/analysis/data/exp1_latency.csv`, `exp2_zero_offset.csv`, `exp3_walking.csv`는 **〔예시〕 값이다(실측 아님).** 예: 반응 시작 292 ms / 도달 602 ms. → 위 실측값으로 바꾼다.
- 예전 산정치: 1단계 변화 약 258 ms, 전체 스트로크 약 615 ms → 실측(116 / 280 ms)으로.
- 핀 스트로크 20.9 mm → **9.0 mm**(단계당 1.29 mm).
- 실외 깊이: Virtual KITTI 2 미터 모델 → **상대 깊이 + 카메라 높이 기준 환산**. 실내: 미터 모델 그대로 → **− 0.44 m 보정**.
- d_far 4 / 8 m → **실내 8 m / 실외 20 m**. 카메라 높이 1.0 m → **0.70 m**.

## 5. 넣지 말 것 · 공개 규칙

- 발표 자료에 넣지 않는다: 실명, 학번, 지도교수 이름, 교수님 리뷰 내용, 이 비공개 저장소의 이름·링크, 이 파일의 내용, 집 안·주차장 거리 사진(`data/raw/distance_*`), 사람 얼굴이 나온 사진·영상.
- 발표 자료나 관련 파일을 **공개 저장소**(예: `MuakTiger/tactile-vision`)에 올릴 때 이 지시 파일, 작업 메모, 붙여 넣은 프롬프트를 함께 올리지 않는다. 공개 커밋 메시지에도 쓰지 않는다. 공개 저장소에 무엇을 올릴지는 올리기 전에 사용자에게 묻는다.
- 공개 장치 코드 링크(`github.com/MuakTiger/tactile-vision`)를 자료에 넣을지도 사용자에게 먼저 묻는다.
- **예비 결과로만 말한다**: 장치 1대, 사진 장소 2곳씩, 구동 지연 17회, 시각장애인 사용자 시험 없음, 보행 시험은 아직. 효과나 임상 성능처럼 쓰지 않는다(예: "proven", "clinically validated" 금지 → "preliminary bench results").
