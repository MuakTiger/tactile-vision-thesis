> 작성 메모 (docx에는 들어가지 않음)
>
> 1. B판(새로 쓴 판, 2026-10-19 iMac): 이전 원고(v1~v3, 양식1)를 바탕으로 하지 않고, 측정 자료(FACTS §1.8~§1.11, analysis/out_*), 장치 코드, 프로젝트 목표를 바탕으로 장치를 평가하는 관점에서 새로 썼다. 핵심은 모든 오차를 '표시 단계'로 바꾸어 비교한 것(`analysis/level_budget.py` → `out_level/`).
> 2. 정지 감지·1인 보행은 자료가 없어 넣지 않았다(사용자 시험은 다음 단계로 서술).
> 3. 그림: `analysis/paper_figures.py` → `figures/final/fig_B*.png`, [그림 2]는 `analysis/hw_figure.py` → `fig_hw_cad.png`(하드웨어 저장소 STL; 착용형 하우징 STL은 설계만 해서 넣지 않음).
> 4. 〔 〕 = 사용자가 채울 곳(docx에서는 노란색): 영문 이름, [23] 커밋 해시.
> 5. docx 만들기: `python thesis/양식/build_docx.py thesis/졸업논문_B_새로쓴판.md`

---
title_ko: 단일 카메라 손바닥 핀 배열 보행 보조 장치의 거리 추정에서 핀 높이까지의 오차·지연 분석
title_en: Error and Latency Analysis from Distance Estimation to Pin Height in a Single-Camera Palm Pin-Array Walking Aid
authors_ko: 오형준 · 하지현
authors_en: 〔Hyeong-Jun Oh · Ji-Hyeon Ha〕
---

## 요약

**목적:** 시각장애인의 혼자 걷기를 돕는 촉각 보조 장치를 카메라 한 대와 범용 부품으로 만들고, 카메라가 본 거리가 손바닥의 핀 높이로 전달되기까지 각 단계에서 생기는 오차와 지연을 같은 기준으로 비교하여 성능을 제한하는 단계를 찾는다. **방법:** 장치는 NVIDIA Jetson Orin Nano에서 Depth Anything V2로 거리를 추정하고(실내: 미터 모델 − 0.44 m, 실외: 상대 깊이의 땅 기준 환산), 6 × 4칸의 거리를 로그 눈금 8단계의 핀 높이로 바꾸어 Raspberry Pi Pico와 서보 24개로 양 손바닥에 표시한다. 네 장소에서 찍은 사진 120장으로 거리 추정을, 실행 기록 7,894프레임으로 처리 시간을, 초당 235프레임 영상 17회로 구동 지연을, 핀별 소프트웨어 보정량으로 24핀의 영점 오차를 재었다. 거리 오차와 높이 오차는 모두 표시 단계(1단계 = 핀 높이 1.29 mm = 거리 실내 1.49배, 실외 1.69배)로 바꾸어 비교하였다. **결과:** 장면별로 보정한 거리 추정의 평균 단계 오차는 실내 0.19단계, 실외 0.35단계로 보정 전(실내 0.70단계, 실외 미터 모델 2.94단계)보다 작았고, 모든 사진이 ±1단계 안에 들었다. 보정 전 핀 영점 오차는 평균 1.25단계(표준편차 2.20 mm, 최대 4.0단계)였고, 같은 거리에서 실내·실외 눈금의 차이는 최대 1.74단계였다. 카메라 프레임이 Jetson에 들어온 뒤 핀이 도착하기까지는 평균 383.7 ms였고 그중 73 %가 Pico의 박자 대기와 서보 이동이었으며, 17회 모두 설계 요구(시작 0.5초, 도착 1초 이내)를 만족하였다. **결론:** 장면별로 보정한 거리 추정 오차는 보정하지 않은 기구 영점 오차와 장면 간 눈금 차이보다 작았고, 지연은 계산보다 구동 박자와 속도 제한이 정하였다. 범용 부품 장치의 성능을 높이려면 깊이 모델과 함께 기구 보정, 눈금 설계, 구동 박자를 다루어야 하며, 손바닥이 한 단계 차이를 구별하는지는 다음 단계에서 측정해야 한다.

**주제어:** 감각 대체, 촉각 디스플레이, 단안 깊이 추정, 오차 분석, 보행 보조기기

## Abstract

**Purpose:** We built a tactile walking aid for people with visual impairment from a single camera and general-purpose parts, and compared, on a common scale, the errors and delays that arise at each stage between the distance seen by the camera and the pin height felt by the palm, in order to identify the stage that limits performance. **Methods:** The device estimates distance with Depth Anything V2 on an NVIDIA Jetson Orin Nano (indoors: metric model minus 0.44 m; outdoors: ground-based scaling of relative depth), maps the distances of 6 × 4 cells to eight logarithmic pin-height levels, and displays them under both palms through a Raspberry Pi Pico and 24 servos. Distance estimation was measured with 120 photographs at four sites, processing time with 7,894 logged frames, actuation latency with 17 trials of 235 frames/s video, and the zero-level error of the 24 pins from per-pin software calibration. All distance and height errors were converted to display levels (one level = 1.29 mm of pin height = a distance ratio of 1.49 indoors and 1.69 outdoors). **Results:** After scene-specific correction, the mean level error of distance estimation was 0.19 levels indoors and 0.35 levels outdoors, smaller than before correction (0.70 levels indoors, 2.94 levels for the outdoor metric model), and every photograph was within ±1 level. Before calibration, the pin zero-level error was 1.25 levels on average (standard deviation 2.20 mm, maximum 4.0 levels), and the indoor and outdoor scales differed by up to 1.74 levels for the same distance. The time from a camera frame reaching the Jetson to pin arrival was 383.7 ms on average, 73 % of which was spent waiting for the Pico update tick and moving the servo; all 17 trials met the design requirement (start within 0.5 s, arrival within 1 s). **Conclusion:** After scene-specific correction, the distance-estimation error was smaller than the uncalibrated mechanical zero-level error and the difference between the indoor and outdoor scales, and latency was governed by actuator pacing and speed limits rather than computation. Improving such low-cost devices should therefore address mechanical calibration, scale design and actuator timing together with depth models, and whether the palm can discriminate a one-level step must be measured next.

**Keywords:** sensory substitution, tactile display, monocular depth estimation, error analysis, mobility aid

## Ⅰ. 서  론

시각장애인이 혼자 걸을 때 필요한 것은 앞쪽 공간 가운데 어느 방향이 얼마나 가까이 막혀 있는지에 대한 정보이다. 세계보건기구는 적어도 22억 명이 시각 손상을 가지고 있다고 보고하였고[1], 2020년 실명 인구는 4,330만 명으로 추정된다[2]. 국내에도 약 25만 명이 시각장애인으로 등록되어 있다[3]. 가장 널리 쓰이는 흰지팡이는 믿을 만하지만 몸 앞의 바닥 가까운 범위만 알려 주어, 지팡이를 쓰는 사람도 허리 위나 머리 높이의 장애물과 부딪히는 사고를 자주 겪는다[4].

다른 감각으로 공간 정보를 전하려는 감각 대체 연구는 카메라 영상을 등에 닿는 400개의 자극기로 옮긴 Bach-y-Rita의 촉각-시각 대체 장치에서 시작되었다[5]. 혀에 전기 자극을 주는 BrainPort는 흰지팡이를 보조하는 기기로 판매 허가를 받았으나[6, 7], 입에 물고 써야 하므로 말하거나 먹는 동안에는 쓰기 어렵다. 초음파나 깊이 카메라로 거리를 재어 소리나 진동으로 알리는 전자 보행 보조기기도 많이 제안되었지만, 대부분 알려 주는 방향이 몇 개뿐이거나 청각을 차지하였고, 사용자 평가까지 이어진 경우는 드물었다[8–10]. 핀의 높이로 정보를 나타내는 촉각 디스플레이는 소리 없이 여러 위치를 동시에 보여 줄 수 있으나, 핀마다 구동기가 필요해 크고 비싸다[11].

최근 단안 깊이 추정 모델은 카메라 한 대의 영상에서 미터 단위 거리를 출력할 수 있게 되었다[12]. 이를 쓰면 깊이 카메라 없이, 취미용 서보와 3D 프린팅 기구 같은 값싼 부품으로 핀 배열 보조 장치를 만들 수 있다. 그러나 이렇게 만든 장치에서 거리 정보는 카메라, 거리 추정, 표시 변환, 통신과 구동, 기구를 차례로 거쳐 손바닥에 닿고, 단계마다 오차와 지연이 더해진다. 단안 영상에서 추정한 절대 거리는 학습 때의 카메라 조건에 따라 배율이 달라질 수 있고[13], 3D 프린팅 기구에는 조립 공차가, 서보 구동에는 갱신 주기와 속도 한계가 있다. 장치 전체의 성능만 재면 이 가운데 어느 단계가 사용자에게 전달되는 정보를 제한하는지 알 수 없다.

본 연구는 카메라 한 대와 범용 부품으로 손바닥 핀 배열 보행 보조 장치를 구현하고, 각 단계의 오차와 지연을 측정하여 핀의 '표시 단계'라는 공통 단위로 비교한다. 평가 기준은 두 가지로 두었다. 첫째, 거리 추정 오차가 표시 단계로 ±1단계 이내인가. 둘째, 가까운 물체가 나타난 뒤 0.5초 안에 핀이 움직이기 시작하고 1초 안에 도착하는가. 1초는 보통 걷는 속도(약 1.2 m/s)에서 약 1.2 m에 해당한다. 사용자가 단계 차이를 구별하고 보행에 활용하는지는 이 공학적 조건을 확인한 뒤의 단계로 남긴다.

## Ⅱ. 연구 방법

### 2.1 연구 대상

평가 대상은 구현한 장치 1대이며, 사람을 대상으로 한 시험은 하지 않았다. 핀 영점 보정(2.3 (4))에서 핀 윗면이 패드 표면과 같은지는 연구자가 눈과 손끝으로 판단하였다.

### 2.2 장치와 정보 경로

장치는 카메라 영상에서 앞쪽 거리를 추정하고, 이를 4행 × 6열 핀의 높이로 바꾸어 양 손바닥에 전달한다. 정보가 지나가는 경로와 각 단계에서 측정한 값은 [그림 1], 단계별 설정은 [표 1]과 같다.

![[그림 1] 장치의 정보 경로와 단계별 측정값. 가운데 열은 구성, 오른쪽 열은 본 연구에서 잰 값이며 회색은 측정하지 않은 단계이다. 단계 오차는 반올림 전 표시 단계 차이의 평균이다](figures/final/fig_B1_path.png){width=7.2}

카메라(Logitech C920)는 패드 앞면에 수평으로 달려 착용 시 렌즈가 땅에서 약 0.70 m에 오며, 1280 × 720, 초당 30프레임으로 영상을 받는다[14]. 자동 초점은 끄고 초점을 고정하였다. 가운데 1280 × 698 영역을 924 × 504로 줄여 쓰며, 이때 세로 반화각은 약 21°이다.

연산은 NVIDIA Jetson Orin Nano Super(25 W 모드)에서 TensorRT FP16으로 한다. Places365[15]로 학습한 ResNet18[16] 분류기가 초당 2회 장면을 판별하여 거리 추정 방식을 고른다. 실외 범주 204개[17]의 확률 합을 시간 상수 1.0초로 평활하고, 0.65 이상 또는 0.35 이하가 1.5초 이어지면 실외 또는 실내로 전환한다. 실내에서는 Hypersim[18]으로 미세조정된 Depth Anything V2[12] ViT-S 미터 모델의 출력에서 0.44 m를 뺀다. 실외에서는 미세조정 전의 상대 깊이 모델을 쓴다. 상대 깊이 r이 거리 Z에 반비례한다고 보면(r = A / Z), 높이 h의 수평 카메라에서 화면 y번째 줄에 보이는 땅의 거리는 Z(y) = f·h / (y − c<sub>y</sub>)이므로(f는 화소 단위 초점거리, c<sub>y</sub>는 가운데 줄), 땅이 1.8~3.5 m에 보이는 줄들에서 r과 Z(y)의 곱의 중앙값으로 프레임마다 A를 정하고 모든 화소의 거리를 A / r로 구한다(땅 기준 환산, h = 0.70 m, f = 908 화소, A는 로그 값을 1.0초로 평활). 두 보정은 2.3 (1)의 측정 결과에 따라 정하였으며, 처음 설계에서 쓴 Virtual KITTI 2[19] 미터 모델은 같은 측정에서 거리를 수 배 멀게 추정하여 빼었다.

깊이 지도를 6 × 4칸으로 나누어 칸마다 화소 거리의 하위 10번째 백분위를 대표 거리 d로 하고, 표시 단계 ℓ(d) = 7 · ln(d<sub>far</sub> / d) / ln(d<sub>far</sub> / 0.5 m)(d는 0.5 m~d<sub>far</sub>로 제한)를 반올림하여 단계 0~7을 얻는다. d<sub>far</sub>는 실내 8 m, 실외 20 m이다. 이 로그 눈금에서 한 단계는 거리의 일정한 배율 (d<sub>far</sub> / 0.5 m)<sup>1/7</sup>에 해당하며, 실내 1.49배, 실외 1.69배이다. 대표 거리는 다가올 때 0.65, 멀어질 때 0.25의 계수로 평활하고, 단계는 올라갈 때 바로, 내려갈 때 3프레임 확인 뒤 한 단계씩 바꾼다. 위험 물체는 YOLO26n[20]으로 찾아 4 m 안에 있는 칸의 핀을 위험도에 따라 1~3° 떨게 한다(초당 10회). 진동은 목표 위치에 더해져 같은 속도 제한을 거치므로, 큰 이동 중에는 이동이 우선한다.

Jetson은 처리가 끝날 때마다 24칸의 단계와 위험도를 31바이트 프레임(CRC-8)으로 USB를 통해 Raspberry Pi Pico[21]에 보낸다. Pico는 0.2초 박자마다 가장 최근 값을 목표로 정하고, 5 ms마다 최대 4 tick씩 서보를 옮긴다. PCA9685[22] 두 개가 SG90 서보 24개를 구동하고, 서보마다 3D 프린팅한 랙·피니언(피치원 지름 16.00 mm)이 회전을 핀의 오르내림으로 바꾼다([그림 2]). 구동 범위 140 tick은 핀 높이 9.0 mm에 해당하므로 한 단계(20 tick)는 1.29 mm이다. 이 범위는 속도 제한으로 끝에서 끝까지 175 ms에 움직여 한 박자 안에 들도록 정한 것이다. 핀 간격은 가로 30 mm, 세로 40 mm이고, 왼쪽 3열은 왼손, 오른쪽 3열은 오른손이 맡는다. 유효한 프레임이 0.5초 동안 없으면 Pico는 모든 핀을 10 ms에 1 tick씩 가장 낮은 위치로 내린다. 장치 코드는 공개하였다[23].

![[그림 2] 촉각 패드와 핀 구동부의 3D 모델(설계 STL). (a) 베이스판과 서보 유닛 24개를 서보 쪽에서 본 모습이다. 손바닥은 반대쪽 평면에 닿고, 핀(랙)은 판의 구멍 24개를 지나 오르내린다. (b) 핀 하나의 구동부. SG90 서보가 12잇수 피니언(피치원 지름 16.00 mm)을 돌려 랙을 오르내리게 한다](figures/final/fig_hw_cad.png){width=7.2}

[표 1] 단계별 구성과 주요 설정값

| 단계 | 구성 | 주요 설정 |
|---|---|---|
| 감지 | Logitech C920 | 1280 × 720, 30 fps, 초점 고정, 렌즈 높이 0.70 m, 세로 반화각 약 21° |
| 거리 추정 | Jetson Orin Nano Super, TensorRT FP16 | 입력 924 × 504, 장면 판별 초당 2회. 실내: 미터 모델 − 0.44 m. 실외: 상대 깊이 + 땅 기준 환산 |
| 표시 변환 | 6 × 4칸 | 하위 10번째 백분위, 로그 8단계, 0.5 m ~ 8 m(실내) / 20 m(실외), 비대칭 시간 필터 |
| 위험 물체 | YOLO26n | 512 × 288, 4 m 이내, 진동 1/2/3°, 초당 10회 |
| 전송 | USB 프레임 | 31바이트, CRC-8, 약 15 Hz |
| 구동 | Pico, PCA9685 × 2, SG90 × 24 | 박자 0.2 s, 5 ms마다 4 tick, 140 tick = 9.0 mm, 1단계 = 20 tick = 1.29 mm |
| 패드 | 4 × 6 핀 | 간격 30 × 40 mm, 왼손 3열·오른손 3열 |
| 안전 | Pico 펌웨어 | 0.5 s 끊김 → 10 ms마다 1 tick씩 하강 |

### 2.3 측정

**(1) 거리 추정.** 장치 카메라를 노트북에 연결해 장치와 같은 초점 설정으로 1280 × 720 무손실 사진을 찍었다. 렌즈는 손수레 위에서 땅에서 약 0.70 m 높이에 두고 눈대중으로 수평을 맞추었다. 표적은 흰 상자의 앞면(가로 30 × 세로 27 cm)이며, 렌즈에서 앞면까지의 거리를 줄자로 재었다. 실외 두 곳(산책로, 주차장)에서 1, 2, 3, 4, 6, 8 m, 실내 두 곳(거실, 주방)에서 0.5, 1, 1.5, 2, 3, 4 m를 거리마다 5장씩 찍어 모두 120장을 얻었다. 사진마다 상자 앞면을 손으로 표시하고, 장치와 같은 전처리를 거친 깊이 지도에서 그 영역을 사방 20 % 줄인 안쪽의 중앙값을 추정 거리로 하였다. 비교한 방법은 미터 모델 두 개(실내 Hypersim, 실외 Virtual KITTI 2)의 보정 전 출력, 실내 모델의 더하기 보정, 땅 기준 환산이다. 실내 보정값은 이 사진들로 정하였으므로, 성능은 한 장소에서 구한 값을 다른 장소에 적용하여(장소 교차) 평가하였다. 땅 기준 환산은 표적 거리를 쓰지 않는다.

**(2) 처리 시간.** 장치는 프레임마다 Jetson이 프레임을 받은 뒤 처리를 시작하기까지의 대기와 단계별 처리 시간을 기록한다. 카메라부터 핀까지 연결해 실내에서 실행한 기록 7,894프레임으로 이를 구하였다. 이 기록은 거리 추정 방식을 바꾸기 전 설정에서 얻은 것이며, 바꾼 뒤의 깊이 추론 시간은 따로 재어 비교하였다. 또 Pico 없이 60초 실행하여 처리율과 Jetson 모듈의 입력 전력을 재었다.

**(3) 구동 지연.** Jetson이 핀 지령을 보낸 뒤 핀이 움직이기까지를 재기 위해, 깊이 추정 없이 칸 하나(위에서 둘째 줄 넷째 칸)의 단계를 0과 7 사이에서 2.5~3.5초 무작위 간격으로 바꾸어 보내고, 바꾸는 순간 모니터 화면을 흰색 또는 검은색으로 바꾸는 시험 프로그램을 썼다. 프레임은 평소처럼 초당 15회 보냈다. 스마트폰(Galaxy S10 5G) 슬로 모션으로 모니터와 핀을 함께 찍고, 화면 밝기가 바뀌는 순간과 핀의 세로 위치(정규화 상호상관 추적, 고정 구조물로 흔들림 보정)를 프레임마다 구하였다. 영상의 실제 촬영 속도는 프로그램 기록과 맞추어 초당 235.05프레임으로 구하였다. 9.0 mm 이동의 5 %를 넘는 순간을 시작, 95 %를 넘는 순간을 도착으로 하고, 보낸 시각부터 화면 갱신 명령이 끝나기까지의 기록 시간을 더해 보낸 시각 기준으로 나타냈다. 손으로 들고 찍은 녹화와 흔들림이 큰 전환을 빼고 17회(올림 8, 내림 9)를 분석하였다. 모니터 표시 지연과 카메라 내부 지연은 포함되지 않아 실제보다 짧게 나온다.

**(4) 핀 영점.** 보정 전에는 24핀이 같은 지령(단계 0 = 372 tick)을 받았다. 핀을 하나씩 골라 단계 0에서 핀 윗면이 패드 표면과 같아질 때까지 tick을 옮기고(주로 5 tick, 1 tick은 약 0.065 mm), 단계 7도 같은 수만큼 옮겨 스트로크를 유지하였다. 옮긴 양을 그 핀의 보정 전 영점 오차로 보았고, 핀을 내린 경우(보정 전에 튀어나온 경우)를 양수로 하였다. 보정 범위는 ±80 tick이었다.

### 2.4 분석

거리 오차는 사진별 절대 백분율 오차의 평균(MAPE)과 함께 표시 단계 단위로도 나타냈다. 실제 거리 d와 추정 거리 d′를 2.2의 식으로 반올림 전 단계 ℓ(d), ℓ(d′)로 바꾸고, 그 차의 절댓값 |Δℓ|의 평균을 구하였다(실내 사진 d<sub>far</sub> 8 m, 실외 사진 20 m). 반올림한 단계의 일치율과 ±1단계 이내 비율도 구하였다. 핀 높이 오차는 한 단계 높이(1.29 mm)로 나누어 단계로 바꾸었다. 반올림 오차는 −0.5~+0.5단계에 고르게 분포한다고 보아 평균 0.25단계로 두었고, 장면별 눈금 차이는 같은 거리에서 ℓ<sub>실외</sub>(d) − ℓ<sub>실내</sub>(d)로 계산하였다. 반응 시간은 프레임별 '대기 + 처리'(7,894프레임)와 시행별 구동 지연(17회)을 따로 잰 뒤 더하였으며, 앞의 것은 평균, 95번째 백분위, 최댓값을 각각 더해 설계 요구를 확인하였다. 실외에서 땅 기준 환산과 실내 모델 − 0.44 m의 비교는, 같은 장면에서 찍은 5장이 독립이 아니므로 장소 × 거리 12묶음의 평균 오차로 윌콕슨 부호순위 검정과 묶음 부트스트랩(10,000회) 95 % 신뢰구간을 구하였다. 계산은 Python(NumPy, pandas, SciPy)으로 하였다.

## Ⅲ. 결  과

### 3.1 거리 추정

방법별 결과는 [표 2], 거리별 추정/실제 비는 [그림 3]과 같다. 실내 모델은 실내 사진에서 모든 거리를 멀게 추정하였고, 그 차이는 거리에 거의 무관하였다(평균 차이 거실 0.47 m, 주방 0.41 m). 이 때문에 추정/실제 비는 0.5 m에서 1.87로 가장 컸고 4 m에서 1.11로 작아졌다. 다른 장소의 평균 차이를 빼면 MAPE는 34.3 %에서 9.5 %로, 평균 단계 오차는 0.70단계에서 0.19단계로 줄었다. 땅 기준 환산은 실내 사진에서 MAPE 54.8 %였다.

실외 사진에서 실외 미터 모델은 1 m를 평균 8.82 m, 8 m를 27.28 m로 추정하여 MAPE 518.5 %, 평균 단계 오차 2.94단계였고, 화면 아래쪽 땅에서도 기하 거리의 3.11~3.69배였다. 실내 모델 − 0.44 m는 산책로에서 6.7 %였으나 주차장에서 69.3 %로 장소에 따라 크게 달랐다. 땅 기준 환산은 MAPE 21.1 %(산책로 10.9 %, 주차장 31.2 %), 평균 0.35단계였고 모든 사진이 ±1단계 안에 들었다. 묶음 단위로 땅 기준 환산의 오차는 실내 모델 − 0.44 m보다 평균 16.9 %p 작았다(95 % 신뢰구간 −32.1 ~ −2.9 %p, 윌콕슨 p = 0.092). 가정한 기울기가 1° 틀리면 땅 기준 환산의 MAPE는 16.8~26.3 %, 3° 틀리면 12.6~41.3 %였다.

[표 2] 거리 추정 방법별 오차

| 방법 | MAPE (%) | 평균 \|Δℓ\| (단계) | 단계 일치 (%) | ±1단계 (%) |
|---|---|---|---|---|
| § 실내 사진 60장 (d<sub>far</sub> 8 m) | | | | |
| 실내 모델 (보정 전) | 34.3 | 0.70 | 60 | 92 |
| 실내 모델 − 차이 (장소 교차) | 9.5 | 0.19 | 75 | 100 |
| 땅 기준 환산 | 54.8 | 0.96 | 57 | 70 |
| 실외 모델 (보정 전) | 460.6 | 3.57 | 0 | 0 |
| § 실외 사진 60장 (d<sub>far</sub> 20 m) | | | | |
| 실외 모델 (보정 전) | 518.5 | 2.94 | 0 | 0 |
| 실내 모델 − 0.44 m | 38.0 | 0.55 | 55 | 92 |
| 땅 기준 환산 | 21.1 | 0.35 | 60 | 100 |

주: |Δℓ|은 실제 거리와 추정 거리를 반올림 전 표시 단계로 바꾼 차이의 절댓값이다. 장치에 쓰는 방법은 실내 사진의 '실내 모델 − 차이'와 실외 사진의 '땅 기준 환산'이다.

![[그림 3] 거리별 추정 거리/실제 거리 비(로그 눈금). (a) 실내 사진, (b) 실외 사진. 점은 두 장소 10장의 기하 평균, 막대는 로그 표준편차, 회색 띠는 그 장면 눈금의 ±1단계(실내 1.49배, 실외 1.69배)이다](figures/final/fig_B2_ratio.png){width=7.2}

### 3.2 처리 시간과 구동 지연

Jetson에서 프레임을 받은 뒤 처리를 시작하기까지의 대기는 평균 34.8 ms, 처리는 평균 68.8 ms였고, 처리 가운데 깊이 추정이 48.5 ms를 차지하였다([표 3]). 대기와 처리를 합한 시간은 평균 103.6 ms, 95번째 백분위 137.4 ms였다. Pico 없이 60초 실행한 처리율은 초당 15.3프레임, Jetson 모듈의 입력 전력은 중앙값 14.4 W였다. 거리 추정 방식을 바꾼 뒤의 깊이 추론 시간(예열 뒤 최솟값)은 실내 39.6 ms, 실외 40.6 ms로 바꾸기 전(39.5 ms)과 1.1 ms 이내였다.

지령을 보낸 뒤 핀이 움직이기 시작하기까지는 평균 116.3 ms였고 41.6~215.7 ms로 넓게 퍼져 있었다(표준편차 54.2 ms). 움직이기 시작해서 도착하기까지는 평균 163.8 ms(표준편차 6.8 ms)로 시행 사이 차이가 작았다. 대기와 처리 시간의 평균을 더하면 반응 시간은 시작 219.9 ms, 도착 383.7 ms였고([그림 4]), 그중 Jetson이 103.6 ms(27 %), 보낸 뒤 Pico와 서보가 280.1 ms(73 %)였다. 대기와 처리의 95번째 백분위를 더해도 시작은 최대 353.1 ms, 도착은 최대 516.6 ms였으며, 최댓값을 더하면 각각 382.4 ms, 545.9 ms로 17회 모두 설계 요구를 만족하였다.

[표 3] 처리 시간과 구동 지연 (ms)

| 구간 | 횟수 | 평균 | 표준 편차 | 95 백분위 | 최대 |
|---|---|---|---|---|---|
| Jetson 대기 | 7,894 | 34.8 | 15.5 | 70.1 | 87.3 |
| Jetson 처리 | 7,894 | 68.8 | 7.3 | 82.4 | 114.4 |
| └ 깊이 추정 | 7,894 | 48.5 | 3.4 | 55.2 | 78.5 |
| 보냄 → 시작 | 17 | 116.3 | 54.2 | 205.9 | 215.7 |
| 시작 → 도착 | 17 | 163.8 | 6.8 | 174.6 | 175.2 |
| 보냄 → 도착 | 17 | 280.1 | 55.8 | 375.6 | 379.2 |

주: Jetson 대기와 처리는 거리 추정 방식을 바꾸기 전 설정의 실행 기록, 나머지는 칸 하나의 단계 0 ↔ 7 이동에서 잰 값이다.

![[그림 4] 반응 시간 구성. 위: 평균 구성(ms). 아래: 시행별 시작·도착 시간(채운 점은 Jetson 대기 + 처리의 평균, 빈 점은 그 95번째 백분위를 더한 값). 빨간 점선은 설계 요구](figures/final/fig_B3_latency.png){width=7.2}

### 3.3 핀 영점

보정 전 영점 오차는 24핀에서 평균 0.00 mm, 표준편차 2.20 mm, 절댓값 평균 1.61 mm(1.25단계), 범위 −3.55 ~ +5.17 mm였다([그림 5]). 보정이 필요 없던 핀은 5개, 한 단계를 넘는 핀은 11개, 두 단계를 넘는 핀은 7개였고 최대는 4.0단계였다. 3 mm를 넘는 오차 6개 가운데 3개는 튀어나온 쪽, 3개는 들어간 쪽이었다. 1행 6열(칸 5)은 보정 범위의 끝까지 옮겼다.

![[그림 5] 핀별 보정 전 영점 오차(mm, 괄호는 단계). 칸 배치는 화면과 같으며 굵은 선 왼쪽은 왼손, 오른쪽은 오른손이 맡는다. + = 보정 전 패드 표면보다 높음](figures/final/fig_B4_pinzero.png){width=7.2}

### 3.4 표시 단계로 바꾼 오차 비교

[표 4]는 측정한 오차를 모두 표시 단계로 바꾸어 나란히 놓은 것이다. 보정한 거리 추정의 평균 오차(0.19, 0.35단계)는 반올림 오차의 평균(0.25단계)과 비슷한 크기였고, 보정 전 핀 영점 오차(평균 1.25단계)와 같은 거리의 장면 간 눈금 차이(1 m에서 0.43단계, 8 m에서 1.74단계)는 이보다 컸다.

[표 4] 표시 단계로 바꾼 오차 원천 비교

| 원천 | 측정값 | 단계 | 근거 |
|---|---|---|---|
| 거리 추정: 실내 모델, 보정 전 | MAPE 34.3 % | 0.70 | 60장 |
| 거리 추정: 실내, 차이 보정 | MAPE 9.5 % | 0.19 | 60장 |
| 거리 추정: 실외 미터 모델 | MAPE 518.5 % | 2.94 | 60장 |
| 거리 추정: 땅 기준 환산 | MAPE 21.1 % | 0.35 | 60장 |
| 핀 영점: 보정 전 | 절댓값 평균 1.61 mm | 1.25 | 24핀 |
| 핀 영점: 보정 조정 걸음 | 0.32 mm | 0.25 | 5 tick |
| 반올림 | − | 평균 0.25 | 설계 |
| 장면 간 눈금 차 (같은 거리) | 1~8 m | 0.43~1.74 | 설계 |

주: 거리 추정과 핀 영점은 평균 절대 단계 차이이다. 보정 뒤 남은 영점 오차는 재지 않았으며, 보정 조정 걸음은 그 상한의 참고값이다.

## Ⅳ. 고  찰

단안 깊이 추정은 이 장치에서 가장 불확실한 단계로 보이기 쉽고, 실제로 보정하지 않은 실외 미터 모델(평균 2.94단계)은 다른 어떤 원천보다 컸다. 그러나 장면별로 보정한 뒤 거리 추정의 평균 오차는 0.19~0.35단계로, 단계를 반올림하면서 생기는 오차와 비슷한 수준이 되었다. 같은 단위로 놓고 보면, 거리 추정을 보정한 뒤에는 그 오차보다 보정하지 않은 3D 프린팅 기구의 영점 오차(평균 1.25단계)와 장면에 따라 바뀌는 눈금의 차이가 더 컸다. 기구 오차는 핀마다 tick을 옮기는 소프트웨어 보정으로 기구를 다시 조립하지 않고 줄일 수 있었다. 범용 부품으로 장치를 만들 때는 부품의 정밀도를 높이기보다 보정 절차를 설계의 일부로 두는 편이 현실적이라는 뜻이다. 다만 보정 뒤 남은 영점 오차는 재지 않았으므로, 그것이 조정 걸음(0.25단계)보다 작은지는 확인이 필요하다.

로그 눈금도 거리 오차를 작게 보이게 하였다. 실외 한 단계는 거리 1.69배에 해당하므로 21.1 %의 평균 오차가 평균 0.35단계에 그쳤고, 가정한 기울기가 3° 틀려 MAPE가 41.3 %가 되어도 대략 0.7단계 수준이다. 반대로 실외 미터 모델처럼 배율 자체가 수 배 틀리면 로그 눈금도 이를 감추지 못한다. 이 모델의 과대 추정은 학습 영상의 카메라 높이(KITTI와 같은 약 1.65 m로 가정)가 장치(0.70 m)보다 높고 화각이 다른 데서 대부분 설명되었으며(계산 배율 약 3.5배, 측정 3.11~3.69배), 단안 영상의 절대 거리가 카메라 조건에 묶인다는 지적[13]과 맞는다. 땅 기준 환산은 알려진 카메라 높이로 배율을 정한다는 점에서 차량 단안 영상의 땅 평면 기반 배율 추정[24, 25]과 같은 원리이며, 착용형 장치에서는 장치를 몸에 다는 높이가 곧 보정값이 된다. 남은 오차(주차장 31.2 %)는 땅이 평평하고 카메라가 수평이라는 가정에서 나오므로, 걷는 동안의 기울기를 관성 센서로 재어 보정하는 것이 다음 과제이다.

지연도 비슷한 구조였다. 깊이 추론은 도착 시간 평균 383.7 ms의 약 13 %(48.5 ms)였고, 73 %는 지령을 보낸 뒤 Pico와 서보에서 생겼다. 움직임 시작까지의 시간이 0.2초 박자 폭만큼 퍼진 것은 Pico가 박자를 기다렸다가 값을 적용하기 때문이며, 평균(116.3 ms)은 박자 대기의 기대값(100 ms)에 약 16 ms가 더해진 정도이다. 핀 이동 시간(163.8 ms)은 펌웨어 속도 제한으로 계산한 5~95 % 이동 시간 157.5 ms와 비슷하여, 서보의 최대 속도가 아니라 펌웨어가 이동 속도를 정하였다. 이 설정값들은 서로 묶여 있다. 1초 안에 도착해야 한다는 요구가 0.2초 박자를 정하고, 한 박자 안에 끝까지 움직이려는 조건이 스트로크 9.0 mm를 정하며, 그 스트로크를 8단계로 나눈 것이 단계 높이 1.29 mm를 정하였다. 따라서 박자를 줄이면 큰 이동이 여러 박자에 나뉘고, 스트로크를 늘려 단계 간격을 키우면 이동 시간이 길어진다. 현재 설정은 요구를 여유 있게 만족하므로(최댓값 합산 545.9 ms), 지연을 더 줄이기보다 이 여유를 단계 간격을 키우는 데 쓰는 것도 고려할 수 있다. 다만 모니터 표시 지연과 카메라 내부 지연은 재지 않아, 실제 여유는 그만큼 작다.

장면별 눈금은 다른 종류의 오차를 만든다. 실외를 20 m까지 표시하면 넓은 공간의 거리감을 전할 수 있지만, 같은 4 m가 실내에서는 1.75단계, 실외에서는 3.05단계가 되어(반올림하면 2와 3) 보정한 거리 추정 오차보다 큰 차이가 생긴다. 감각 대체는 훈련으로 익히는 기술이므로[26], 장면이 바뀔 때마다 같은 거리가 다른 높이로 바뀌면 사용자가 익힐 규칙이 늘어난다. 거리 범위를 하나로 고정하는 것과 장면 전환을 짧은 핀 신호로 알리는 것 가운데 어느 쪽이 나은지는 사용자 시험으로 정할 문제이다.

마지막 단계인 손바닥은 재지 않았다. 핀 간격(30 × 40 mm)은 손바닥의 두 점 구별 거리(1 cm 안팎)[27]보다 넓어 공간 해상도는 피부보다 핀 개수가 제한하지만, 손바닥이 1.29 mm의 높이 차이를 구별하는지는 이번 연구에서 확인하지 않았다. 위험 물체 진동(1~3°, 핀 높이로 약 0.13~0.39 mm)도 서보가 작은 명령에 반응하지 않는 범위에 가깝고, 초당 10회로 손바닥이 가장 예민한 진동 대역보다 낮다[28]. 사용 방식의 문제도 남는다. 패드는 두 손바닥을 모두 쓰므로 한 손에 흰지팡이를 쥐면 절반만 읽을 수 있다. 통신이 끊기면 핀이 가장 낮은 위치로 내려가 '앞이 비었다'는 표시와 구별되지 않으므로 고장을 알리는 별도의 신호가 필요하다. 또 렌즈 높이 0.70 m에서는 앞쪽 1.8 m 안의 바닥, 1 m 앞에서 높이 32 cm 미만인 물체, 2.1~2.6 m보다 가까운 머리 높이(1.5~1.7 m)의 물체가 화면 밖에 있다. 가까운 머리 높이 물체는 화면을 벗어난 뒤에도 비대칭 필터의 느린 하강으로 잠시 표시가 남지만, 장치는 흰지팡이를 대신하기보다 지팡이가 닿지 않는 높이와 거리를 보완하는 역할에 맞다.

본 연구의 한계로, 거리 측정은 실내·실외 두 곳씩의 정지 사진에 그쳤고, 구동 지연은 칸 하나에서 단계 0과 7 사이의 이동만 재었으며, 처리 시간은 거리 추정 방식을 바꾸기 전 설정에서 측정하였다. 또 장치 한 대만 평가하였고, 사람을 대상으로 한 시험은 하지 않았다.

## Ⅴ. 결  론

카메라 한 대와 범용 부품으로 만든 손바닥 핀 배열 보행 보조 장치에서, 거리 정보가 핀 높이로 전달되는 경로를 단계별로 측정하고 오차를 표시 단계라는 공통 단위로 비교하였다. 장면별로 보정한 거리 추정은 평균 0.19~0.35단계의 오차로 모든 사진에서 ±1단계 안에 들었고, 반응 시간은 17회 모두 시작 0.5초, 도착 1초 요구를 만족하였다. 보정한 거리 추정 오차는 보정하지 않은 기구 영점 오차(평균 1.25단계)와 장면 간 눈금 차이(최대 1.74단계)보다 작았고, 지연의 73 %는 Pico의 박자와 서보 이동에서 생겼다. 따라서 이 장치를 개선할 때에는 더 큰 깊이 모델보다 기구 보정 절차, 장면 사이 표시 눈금의 일관성, 박자와 스트로크의 조정을 먼저 다루어야 한다. 다음 단계는 손바닥의 단계 구별 시험과 흰지팡이와 함께 쓰는 보행 시험이다. 장치 코드는 공개하여 같은 부품으로 다시 만들고 검증할 수 있게 하였다[23].

## 참고문헌

[1] World Health Organization, “Blindness and vision impairment,” Fact sheet, Feb. 2026. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/blindness-and-visual-impairment

[2] GBD 2019 Blindness and Vision Impairment Collaborators and Vision Loss Expert Group of the Global Burden of Disease Study, “Trends in prevalence of blindness and distance and near vision impairment over 30 years: an analysis for the Global Burden of Disease Study,” *The Lancet Global Health*, vol. 9, no. 2, pp. e130–e143, 2021. https://doi.org/10.1016/S2214-109X(20)30425-3

[3] 보건복지부, “2023년 등록장애인 현황,” 2024년 4월 발표. 보도: J. Lee, “5.1% of Korean population registered as disabled in 2023: report,” *The Korea Herald*, Apr. 18, 2024.

[4] R. Manduchi and S. Kurniawan, “Mobility-related accidents experienced by people with visual impairment,” *Insight: Research and Practice in Visual Impairment and Blindness*, vol. 4, no. 2, pp. 44–54, 2011.

[5] P. Bach-y-Rita, C. C. Collins, F. A. Saunders, B. White, and L. Scadden, “Vision substitution by tactile image projection,” *Nature*, vol. 221, no. 5184, pp. 963–964, 1969. https://doi.org/10.1038/221963a0

[6] U.S. Food and Drug Administration, “De Novo classification request for BrainPort V100 (DEN130039),” Jun. 2015.

[7] P. Grant, L. Spencer, A. Arnoldussen, R. Hogle, A. Nau, J. Szlyk, J. Nussdorf, D. C. Fletcher, K. Gordon, and W. Seiple, “The functional performance of the BrainPort V100 device in persons who are profoundly blind,” *Journal of Visual Impairment & Blindness*, vol. 110, no. 2, pp. 77–88, 2016. https://doi.org/10.1177/0145482X1611000202

[8] D. Dakopoulos and N. G. Bourbakis, “Wearable obstacle avoidance electronic travel aids for blind: a survey,” *IEEE Transactions on Systems, Man, and Cybernetics, Part C*, vol. 40, no. 1, pp. 25–35, 2010. https://doi.org/10.1109/TSMCC.2009.2021255

[9] W. Elmannai and K. Elleithy, “Sensor-based assistive devices for visually-impaired people: current status, challenges, and future directions,” *Sensors*, vol. 17, no. 3, art. 565, 2017. https://doi.org/10.3390/s17030565

[10] R. K. Katzschmann, B. Araki, and D. Rus, “Safe local navigation for visually impaired users with a time-of-flight and haptic feedback device,” *IEEE Transactions on Neural Systems and Rehabilitation Engineering*, vol. 26, no. 3, pp. 583–593, 2018. https://doi.org/10.1109/TNSRE.2018.2800665

[11] F. Vidal-Verdú and M. Hafez, “Graphical tactile displays for visually-impaired people,” *IEEE Transactions on Neural Systems and Rehabilitation Engineering*, vol. 15, no. 1, pp. 119–130, 2007. https://doi.org/10.1109/TNSRE.2007.891375

[12] L. Yang, B. Kang, Z. Huang, Z. Zhao, X. Xu, J. Feng, and H. Zhao, “Depth Anything V2,” in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 37, pp. 21875–21911, 2024. https://doi.org/10.52202/079017-0688

[13] W. Yin, C. Zhang, H. Chen, Z. Cai, G. Yu, K. Wang, X. Chen, and C. Shen, “Metric3D: Towards zero-shot metric 3D prediction from a single image,” in *Proc. IEEE/CVF International Conference on Computer Vision (ICCV)*, 2023, pp. 9009–9019. https://doi.org/10.1109/ICCV51070.2023.00830

[14] Logitech, “HD Pro Webcam C920 technical specifications.” [Online]. Available: https://support.logi.com

[15] B. Zhou, A. Lapedriza, A. Khosla, A. Oliva, and A. Torralba, “Places: A 10 million image database for scene recognition,” *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 40, no. 6, pp. 1452–1464, 2018. https://doi.org/10.1109/TPAMI.2017.2723009

[16] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image recognition,” in *Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 770–778. https://doi.org/10.1109/CVPR.2016.90

[17] CSAILVision, “Places365: The 365 scene categories and pretrained CNNs.” [Online]. Available: https://github.com/CSAILVision/places365

[18] M. Roberts, J. Ramapuram, A. Ranjan, A. Kumar, M. A. Bautista, N. Paczan, R. Webb, and J. M. Susskind, “Hypersim: A photorealistic synthetic dataset for holistic indoor scene understanding,” in *Proc. IEEE/CVF International Conference on Computer Vision (ICCV)*, 2021, pp. 10892–10902. https://doi.org/10.1109/ICCV48922.2021.01073

[19] Y. Cabon, N. Murray, and M. Humenberger, “Virtual KITTI 2,” arXiv:2001.10773, 2020. https://doi.org/10.48550/arXiv.2001.10773

[20] Ultralytics, “Ultralytics YOLO26.” [Online]. Available: https://docs.ultralytics.com/models/yolo26/

[21] Raspberry Pi Ltd, “RP2040 Datasheet: A microcontroller by Raspberry Pi.” [Online]. Available: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf

[22] NXP Semiconductors, “PCA9685: 16-channel, 12-bit PWM Fm+ I²C-bus LED controller,” Product data sheet, Rev. 4, 2015.

[23] 오형준, “tactile-vision: 단안 깊이 추정 기반 촉각 보행 보조 장치,” GitHub 저장소, 커밋 〔ground-scale 가지 공개 후 기입〕, 2026. [Online]. Available: https://github.com/MuakTiger/tactile-vision

[24] S. Song and M. Chandraker, “Robust scale estimation in real-time monocular SFM for autonomous driving,” in *Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2014, pp. 1566–1573. https://doi.org/10.1109/CVPR.2014.203

[25] D. Zhou, Y. Dai, and H. Li, “Ground-plane-based absolute scale estimation for monocular visual odometry,” *IEEE Transactions on Intelligent Transportation Systems*, vol. 21, no. 2, pp. 791–802, 2020. https://doi.org/10.1109/TITS.2019.2900330

[26] P. Bach-y-Rita and S. W. Kercel, “Sensory substitution and the human–machine interface,” *Trends in Cognitive Sciences*, vol. 7, no. 12, pp. 541–546, 2003. https://doi.org/10.1016/j.tics.2003.10.013

[27] S. Weinstein, “Intensive and extensive aspects of tactile sensitivity as a function of body part, sex, and laterality,” in *The Skin Senses*, D. R. Kenshalo, Ed. Springfield, IL, USA: Charles C. Thomas, 1968, pp. 195–222.

[28] K. O. Johnson, “The roles and functions of cutaneous mechanoreceptors,” *Current Opinion in Neurobiology*, vol. 11, no. 4, pp. 455–461, 2001. https://doi.org/10.1016/S0959-4388(00)00234-8
