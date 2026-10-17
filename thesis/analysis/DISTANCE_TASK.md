# 젯슨 작업 지시 — 거리 정확도 분석 (2026-10-17 작성)

노트북 Claude Code 세션에서 썼다. 사진은 `thesis/analysis/data/raw/distance_20261017/` 아래 4개 폴더, **촬영 끝(120장)**:

| 폴더 | 환경 | 거리(m) × 5장 |
|---|---|---|
| `site1_outdoor/`, `site2_outdoor/` | 실외 2곳 | 1 · 2 · 3 · 4 · 6 · 8 |
| `site1_indoor/`, `site2_indoor/` | 실내 2곳 | 0.5 · 1 · 1.5 · 2 · 3 · 4 |

촬영 조건·장소별 주의점은 그 폴더의 `NOTES.md`. 거리 표시는 노트북에서 장소마다 몇 장(거리 3~5개)을 골라 상자 픽셀 폭으로 역산해 확인했다(NOTES). 120장 전부를 본 것은 아니다.

## 0. 젯슨 Claude Code에 붙여 넣을 프롬프트

```text
내 졸업 프로젝트의 거리 정확도 실험 분석을 이어서 해 줘.
1) ~/github/tactile-vision-thesis 와 ~/tactile-vision 을 git pull 해.
2) 이 순서로 읽어: thesis/analysis/DISTANCE_TASK.md(이 작업 지시, 전부) →
   thesis/analysis/data/raw/distance_20261017/NOTES.md → HANDOFF.md 맨 위 절들 → FACTS.md.
3) DISTANCE_TASK.md 의 '준비 확인'을 먼저 하고 결과를 5줄 이내로 알려 줘.
   그다음 방법 A(클릭)와 방법 B(ROI) 중 무엇부터 할지 나한테 물어봐. 둘 다 할 거야.
4) 규칙: 한국어로 짧게. 장치 설정(config, calib) 바꾸지 않기. 핀을 움직이는 명령 실행하지 않기.
   make_example_data.py 다시 돌리지 않기. 커밋·push 는 나한테 묻고 하기.
```

## 1. 목표
같은 사진을 실내(Hypersim)·실외(Virtual KITTI 2) 두 metric 깊이 모델에 넣고, 표적(흰 상자 앞면 30×27 cm)까지 추정 거리와 줄자 거리를 비교한다.
- 거리별 오차(m, %), 반복 5장의 평균·표준편차
- 모델별 보정 배율 k (참 거리 ≈ k × 추정 거리, 원점 지나는 최소제곱 k = Σ(t·e)/Σ(e²))
- 보정 검증 2가지: 같은 장소 안에서 거리를 하나씩 빼고 맞춤(leave-one-distance-out), **장소 교차**(장소 1로 맞춘 k를 장소 2에 적용, 반대도)
- 보정 전·후 평균 절대 백분율 오차(MAPE)
- 주 비교는 실외 사진 ↔ 실외 모델, 실내 사진 ↔ 실내 모델. 반대 조합은 보조 자료
- 거리 보정 계수는 **분석에서만** 쓴다. 장치 설정에 넣지 않는다(HANDOFF 설정 동결)
- 참고: 예비 분석에서 실외 모델이 실내 모델보다 2.38~2.64배 멀게 봤고, 실외 모델 과대 추정이 알려진 문제(HANDOFF 남은 일 4)

## 2. 준비 확인
1. 두 TensorRT 엔진이 있는지: `tools/compare_models.py`가 찾는 경로(없으면 `python tools/build_engine.py --spec wide` 와 `--spec wide --outdoor`. 빌드는 오래 걸리니 먼저 물어보기)
2. 사진 수: 4개 폴더 각 30장, 각 `shots.csv` 30줄(합 120)
3. 화면(DISPLAY) 있는지 — 방법 A와 B의 표시 단계는 창이 필요하다. 1920 폭 화면이면 `compare_models.py --scale 0.9`
4. 전처리 확인: 장치와 같은 1280×720 → 가운데 1280×698 → 924×504(`compare_models.py`의 `ImageSource`가 `crop_rect` 후 INTER_AREA 축소). 깊이맵 크기도 924×504인지 확인

## 3. 방법 A — 클릭해서 읽기 (새 코드 없음, 사용자가 직접)
기존 `tools/compare_models.py`를 폴더마다 실행한다(4번, 각 30장).

```bash
cd ~/tactile-vision
D=~/github/tactile-vision-thesis/thesis/analysis/data/raw/distance_20261017
python tools/compare_models.py --source $D/site1_outdoor --out-dir logs/dist_site1_outdoor
python tools/compare_models.py --source $D/site2_outdoor --out-dir logs/dist_site2_outdoor
python tools/compare_models.py --source $D/site1_indoor  --out-dir logs/dist_site1_indoor
python tools/compare_models.py --source $D/site2_indoor  --out-dir logs/dist_site2_indoor
```
- 0.5 m 사진은 상자가 화면 대부분을 덮는다. 상자 앞면 가운데(가장자리 말고)를 클릭.

사진마다: **상자 앞면 가운데를 왼쪽 클릭 → `s` 저장 → `n` 다음 사진**.
- 클릭 지점 5×5 픽셀 중앙값을 두 모델 값으로 `probes.csv`에 한 줄 쓴다(`source` 열에 파일 이름, `indoor_probe_m`, `outdoor_probe_m`).
- **주의: 클릭 지점은 다음 사진으로 넘어가도 남는다.** 사진마다 다시 클릭한 뒤 `s`. 표적 없는 사진이면 오른쪽 클릭(해제) 뒤 `n`만.
- `s`는 PNG 3장과 npz도 같이 저장한다(사진당 몇 MB). 끝나면 `probes.csv`만 논문 저장소로 옮겨도 된다.
- 끝나면 Claude가 `probes.csv` 4개를 읽어 `source`의 파일 이름에서 환경·거리를 꺼내고(`<outdoor|indoor>_<거리>m_…`, `0p5`=0.5, `1p5`=1.5) 1절 통계를 낸다. 한 사진에 여러 줄이면 마지막 줄을 쓴다. 장소는 `--out-dir` 폴더 이름으로 구분.

## 4. 방법 B — ROI(상자 영역) 자동 계산
1. 영역 표시(사용자, 화면 필요, 120장 약 10~20분. 4개 폴더를 한 번에 차례로 띄움):
   ```bash
   cd ~/github/tactile-vision-thesis
   python thesis/analysis/annotate_roi.py thesis/analysis/data/raw/distance_20261017
   ```
   사진마다 상자 앞면을 드래그(가장자리 바깥 배경이 안 들어가게 살짝 안쪽) → space. 표적 없으면 `c`. 중간에 끊어도 `rois.csv`에 저장돼 이어서 된다. 좌표는 원본 1280×720 기준.
   - 자동 검출은 쓰지 않는다(10/17 노트북 시험: 가까운 거리에서 바닥을, 그늘에서는 상자를 못 잡음).
2. 분석 스크립트(Claude가 새로 작성): `thesis/analysis/distance_analysis.py`
   - 장치 코드(`~/tactile-vision/src`)의 `crop_rect`, `DepthEngine`, 설정 로드를 재사용(`compare_models.py`가 모델 2개를 만드는 방식 그대로: `max_depth_m` 실내 20, 실외 80)
   - ROI 변환: x' = x × 924/1280, y' = (y − 11) × 504/698 (가운데 698행 크롭이므로 위 11행 제외. `crop_rect` 결과로 계산해 확인)
   - 값: ROI를 사방 20% 줄인 안쪽의 깊이 **중앙값**. 보조로 ROI 가운데가 속한 셀(6×4)의 장치 대표값(하위 10%)
   - 출력 CSV `thesis/analysis/data/exp_distance.csv`: `example`(=0), `method`(roi|click), `env`(outdoor|indoor), `site`, `file`, `shot`, `true_m`, `model`(indoor|outdoor), `est_m`, `cell_p10_m`. 방법 A의 `probes.csv`도 같은 형식(`method=click`)으로 합친다
   - 요약 표·그림은 `thesis/analysis/out_distance/`: 추정 대 실제(y=x 선, 모델·장소별), 거리별 오차 % 보정 전·후, k 표(장소별·합침·교차)
   - 확인용: 사진마다 ROI를 그린 작은 모음 이미지 1~2장 → 사용자에게 보여 주고 ROI가 상자에 맞는지 확인받기
3. 방법 A와 B 값이 크게 다르면(예: 10% 넘게) 그 사진을 보여 주고 원인을 사용자와 같이 본다.

## 5. 끝나면
- 결과를 7줄 이내로: 모델별 보정 전 MAPE, k, 보정 후 MAPE(LODO·장소 교차), 눈에 띄는 거리
- HANDOFF 맨 위에 결과 한 절, FACTS 에 확정 수치(출처 파일·커밋)
- 커밋·push 는 사용자에게 묻고
