> 작성 메모 (docx에는 들어가지 않음. 제출 전 이 상자를 지워도 된다)
>
> 1. C판(2026-10-19, Kiro): `졸업논문_양식1.md`를 바탕으로 틀린 곳을 고치고 Ⅳ 고찰·Ⅴ 결론·요약 결과를 보태 완성한 판. 바뀐 점은 `졸업논문_C_보완목록.md`.
> 2. 수치 근거표는 `.agents/tasks/thesis-cd-2026-10-19/numbers_C.md`, 참고문헌 확인 기록은 `refs_C.md`. 새로 계산한 값은 `analysis/kiro_C_check.py` → `analysis/out_kiro_C/`.
> 3. 보행 실험(정지 감지·1인 보행)은 자료가 없어 목적·방법·결과에서 빼고 고찰의 후속 연구로만 적었다.
> 4. 노란 칸(〔 〕)은 사용자가 채울 곳: 영문 이름, [29] 커밋 해시, 머리말의 회차·연도.
> 5. docx: `python3 thesis/양식/build_docx_C.py thesis/졸업논문_C_완성판.md` (원본 build_docx.py에 머리말 노란 강조만 더한 복사본).
> 6. 2026-10-19 저녁 점검 회차에서 고친 곳은 `졸업논문_C_보완목록.md` 8절.

---
title_ko: 단안 카메라 거리 추정을 이용한 24핀 손바닥 촉각 보행 보조 장치의 구현과 예비 평가
title_en: Implementation and Preliminary Evaluation of a 24-Pin Palm Tactile Walking Aid Using Monocular Camera Distance Estimation
authors_ko: 오형준  ·  하지현
authors_en: 〔영문 이름 표기 — 사용자 입력〕
---

## 요약

**목적:** 일반 카메라 한 대로 추정한 앞쪽 공간의 방향별 거리를 양 손바닥 아래 24개 핀의 높이로 전달하는 착용형 시각-촉각 보행 보조 장치를 구현하고, 그 거리 추정과 구동 성능을 예비적으로 평가한다. **방법:** NVIDIA Jetson Orin Nano에서 Depth Anything V2로 거리를 추정하되, 실내에서는 미터 단위 실내 모델의 출력에서 0.44 m를 빼고, 실외에서는 상대 깊이를 카메라 높이와 화면 속 땅의 위치로 미터로 바꾸었다(땅 기준 환산). 6 × 4칸의 거리는 로그 눈금 8단계의 핀 높이(0~9.0 mm)로 바꾸었다. 네 장소에서 찍은 사진 120장의 추정 거리를 줄자 거리와 비교하고, 처리 시간 기록과 초당 240프레임 촬영으로 반응 시간을, 핀별 영점 보정량으로 조립에 따른 영점 오차를 구하였다. **결과:** 실내 모델의 평균 절대 백분율 오차(MAPE)는 34.3 %였고 다른 장소에서 정한 평균 차이를 빼면 9.5 %가 되었다. 실외 미터 모델은 거리를 크게 멀게 추정하였으나(MAPE 518.5 %), 땅 기준 환산은 21.1 %였고 표시 단계가 모두 ±1단계 안에서 일치하였다. 핀은 지령 뒤 평균 116.3 ms에 움직이기 시작하여 280.1 ms에 도착하였고, 처리 시간의 95번째 백분위를 더해도 17회 모두 시작 0.5초, 도달 1초 안이었다. 보정 전 영점 오차는 표준편차 2.20 mm였고 가장 큰 오차는 네 단계에 해당하였다. **결론:** 일반 카메라와 범용 부품으로, 정지 장면의 거리를 한 단계 안팎의 오차로 표시하고 설계한 시간 안에 반응하는 장치를 구현하였다. 핀별 영점 보정이 필수적이었으며, 걸을 때의 정확도와 보행 보조 효과는 보행 시험으로 확인해야 한다.

**주제어:** 감각 대체, 촉각 디스플레이, 단안 깊이 추정, 시각장애, 보행 보조기기

## Abstract

**Purpose:** This study implements a wearable visual-to-tactile walking aid that conveys the distance of the space ahead, estimated with a single ordinary camera, as the heights of 24 pins under both palms, and preliminarily evaluates its distance estimation and actuation. **Methods:** Distance was estimated with Depth Anything V2 on an NVIDIA Jetson Orin Nano: indoors, 0.44 m was subtracted from the metric indoor model; outdoors, relative depth was converted to metres from the camera height and the position of the ground in the image (ground-based scaling). The distance of each of 6 × 4 cells was mapped on a logarithmic scale to eight pin heights (0–9.0 mm). Estimates from 120 photographs taken at four sites were compared with tape-measured distances; the response time was obtained from processing logs and 240 frames/s video, and the zero-level error from per-pin calibration offsets. **Results:** The mean absolute percentage error (MAPE) of the indoor model was 34.3 %, and 9.5 % after subtracting the mean difference determined at the other site. The outdoor metric model greatly overestimated distances (MAPE 518.5 %), whereas ground-based scaling gave 21.1 %, with every displayed level within ±1 level. Pins started to move 116.3 ms and arrived 280.1 ms after the command on average; with the 95th-percentile processing time added, all 17 trials started within 0.5 s and arrived within 1 s. Before calibration, the zero-level error had a standard deviation of 2.20 mm, the largest corresponding to four levels. **Conclusion:** With an ordinary camera and commodity parts, a device was implemented that displays distances in static scenes within about one level and responds within the designed time. Per-pin zero calibration was essential; accuracy while walking and the effect on walking remain to be verified in walking trials.

**Keywords:** sensory substitution, tactile display, monocular depth estimation, visual impairment, mobility aid

## Ⅰ. 서  론

세계보건기구(WHO)는 전 세계에서 적어도 22억 명이 근거리 또는 원거리 시각 손상을 가지고 있다고 보고하였고[1], 세계질병부담(GBD) 연구는 2020년 실명 인구를 4,330만 명으로 추정하였다[2]. 국내에서도 2023년 등록장애인의 9.4 %인 약 25만 명이 시각장애인이다[3]. 시각장애인이 혼자 걸을 때 필요한 것은 앞쪽 공간의 어느 방향이, 어느 높이에서, 얼마나 가까이 막혀 있는지에 대한 정보이다. 흰지팡이는 몸 앞의 바닥 가까운 영역만 알려 주므로, 가슴 높이 이상의 물체와 부딪히는 사고는 흰지팡이나 안내견을 쓰는 사람에게도 흔하다[4].

이를 다른 감각으로 보완하려는 시도가 감각 대체(sensory substitution)이다. Bach-y-Rita 등은 카메라 영상을 등에 놓인 400개의 진동 자극기로 전달하여, 선천성 시각장애인이 훈련 뒤 자극만으로 물체와 그 배치를 구별할 수 있음을 보였다[5]. 이후 시각장애인의 시각 피질이 점자 읽기나 혀 전기 자극 같은 촉각 과제에 쓰인다는 신경가소성 연구가 이를 뒷받침하였다[6, 7]. 혀에 전극 400개를 놓는 BrainPort V100은 흰지팡이나 안내견을 보조하는 기기로 미국 식품의약국(FDA)의 판매 허가를 받았고[8, 9], 영상을 소리로 바꾸는 vOICe도 제안되었다[10].

그러나 기존 전자 보행 보조기기는 대개 한 방향의 거리만 알리거나, 몇 개 방향의 진동처럼 해상도가 낮거나, 소리를 써서 주변 소리를 듣는 데 필요한 청각을 차지하였으며, 사용자 평가와 일상 사용으로 이어진 경우도 드물었다[11–13]. 핀의 높이로 모양을 보여 주는 촉각 디스플레이는 정적인 높이로 정보를 전할 수 있으나 핀마다 구동기가 필요하여 크고 비싸다[14]. 거리를 얻는 방법도 제약이었다. 깊이 카메라는 비싸고, 적외선을 쓰는 방식은 햇빛 아래에서 성능이 떨어질 수 있다. 일반 카메라 한 대로 거리를 추정하는 범용 모델은 대개 장면 안의 앞뒤 관계만 출력하였고, 미터 단위 출력은 학습 영상을 찍은 카메라의 초점거리 같은 조건에 묶여 다른 카메라에 그대로 쓰기 어려웠다[15]. 최근 공개된 Depth Anything V2는 미터 단위 거리를 출력하는 실내용·실외용 모델을 함께 제공한다[16]. 다만 이런 모델이 보행 높이의 카메라에서 실제로 얼마나 정확한지, 범용 부품으로 만든 핀 배열이 얼마나 빠르고 고르게 움직이는지는 확인되지 않았다.

본 연구의 목적은 일반 카메라 한 대와 범용 부품으로, 앞쪽 공간의 방향별 거리를 양 손바닥 아래 24개 핀의 높이로 전달하는 착용형 장치를 구현하고 그 성능을 예비적으로 평가하는 것이다. 구체적으로 (1) 장치 카메라로 찍은 실내·실외 장면에서 거리 추정 오차와 그 보정 방법, (2) Jetson이 카메라 프레임을 받은 뒤 핀이 움직이기까지의 반응 시간, (3) 24개 핀의 영점 높이 오차(핀별 소프트웨어 보정량)를 구한다. 반응 시간의 설계 요구는 물체가 나타난 뒤 0.5초 안에 핀이 움직이기 시작하고 1초 안에 목표 높이에 이르는 것으로 두었다. 걷는 속도를 1.2 m/s로 가정하면 1초는 약 1.2 m에 해당한다. 장치를 착용하고 걷는 시험은 이번 연구에 포함하지 않았으며, 고찰에서 후속 연구로 다룬다.

## Ⅱ. 연구 방법

### 2.1 연구 대상

본 연구의 평가 대상은 구현한 장치 한 대이며, 사람을 참여자로 하는 실험은 하지 않았다. 거리 정확도는 장치 카메라로 찍은 사진 120장으로, 처리 시간·반응 시간·핀 영점 오차는 장치의 실행 기록, 촬영 영상, 보정 기록으로 평가하였다(2.3). 핀 영점 보정에서 높이가 맞는지는 연구자가 눈과 손끝으로 판단하였다.

### 2.2 장치 구성

장치는 카메라, 연산부, 제어부, 촉각 패드로 이루어진다([그림 1]). 카메라(Logitech C920)[17]는 패드 앞면에 수평으로 달았고(착용 시 렌즈 높이 땅에서 약 0.70 m), 1280 × 720, 초당 30프레임으로 영상을 받는다. 걷는 동안 초점이 바뀌지 않도록 자동 초점을 끄고 초점을 무한대 쪽 끝으로 고정하였다. 연산부는 NVIDIA Jetson Orin Nano Super(메모리 8 GB, 25 W 모드)이며, 깊이 모델과 물체 검출 모델은 TensorRT FP16 엔진으로 실행한다.

![[그림 1] 장치 구성. 각 부의 설정값은 [표 1]과 같다](figures/kiro_C/fig_C1_system.png){width=6.8}

영상은 가운데 1280 × 698 영역을 924 × 504로 줄여 쓴다. 장면 판별은 Places365[18]로 학습한 ResNet18[19] 분류기가 초당 2회 하며, 실외로 분류된 범주 204개[20]의 확률을 더한 값을 시간 상수 1.0초로 평활하여, 0.65 이상이 1.5초 이어지면 실외, 0.35 이하가 1.5초 이어지면 실내로 판정한다. 깊이 추정에는 Depth Anything V2[16]의 ViT-S 모델을 쓴다. 실내로 판정되면 Hypersim[21]으로 학습된 미터 단위 모델의 출력에서 0.44 m를 빼서 쓴다. 이 값은 거리 정확도 실험(2.3 (2))의 실내 사진에서 이 모델이 실제보다 멀게 추정한 거리의 평균 차이이다. 실외로 판정되면 미터 단위로 미세조정하기 전의 상대 깊이 모델을 쓰고, 거리의 배율은 카메라 높이로 정한다(땅 기준 환산). 처음 설계에서는 Virtual KITTI 2[22]로 학습된 실외 미터 단위 모델을 썼으나, 같은 실험에서 이 모델이 보행 높이 영상의 거리를 여러 배 멀게 추정하여(3.2) 바꾸었다.

땅 기준 환산은 알려진 카메라 높이와 땅 평면으로 단안 영상의 거리 배율을 정하는 방법으로, 차량의 단안 주행 거리 추정에서 쓰여 왔다[23, 24]. 본 연구는 이를 프레임마다 상대 깊이 지도 한 장에 적용하였다. 상대 깊이 r이 깊이 Z에 반비례한다고 보고(r = A / Z), 카메라가 땅에서 높이 h에 수평으로 달려 있으면 화면 y번째 줄에 보이는 땅까지의 깊이가 Z(y) = f·h / (y − c<sub>y</sub>)라는 관계를 쓴다(f는 화소 단위 초점거리, c<sub>y</sub>는 화면 가운데 줄). 프레임마다 땅까지 1.8~3.5 m에 해당하는 화면 아래쪽 줄들에서 줄별 r의 중앙값에 Z(y)를 곱하고, 그 중앙값을 A로 하여 모든 화소의 거리를 A / r로 구한다. h는 0.70 m, f는 908 화소(1280 × 720 기준, 표적 크기로 확인)로 두었고, 걸을 때의 흔들림을 줄이도록 A의 로그 값을 시간 상수 1.0초로 평활한다. 이 방식은 땅이 평평하고 화면 아래쪽에 보인다고 가정한다.

깊이맵은 가로 6 × 세로 4칸으로 나누고, 칸마다 화소 거리의 하위 10번째 백분위를 대표 거리 d로 삼는다. 평균을 쓰면 칸의 일부만 차지하는 기둥이나 사람이 먼 배경에 묻히고, 최솟값을 쓰면 화소 하나의 잡음에 핀이 흔들리므로, 칸 넓이의 약 10 %를 차지하는 물체부터 반영되도록 정한 설계값이다(별도로 최적화하지는 않았다). d는 근접도 p = ln(d<sub>far</sub> / d) / ln(d<sub>far</sub> / 0.5 m)로 바꾸고, 7p를 반올림하여 단계 0~7을 얻는다. 가장 먼 표시 거리 d<sub>far</sub>는 실내 8 m, 실외 20 m로 두었다. 걷는 속도를 1.2 m/s로 가정하면 각각 약 7초와 17초 앞에 해당하며, 실외는 공간이 넓어 먼 건물이나 트인 방향까지 거리감을 전하도록 실내보다 멀리 표시한다. 단계를 반올림하므로 핀이 올라오기 시작하는 거리는 실내 6.6 m, 실외 15.4 m이고, 한 단계마다 거리는 실내 약 1.49배, 실외 약 1.69배씩 커진다. 대표 거리는 가까워질 때 0.65, 멀어질 때 0.25의 계수로 지수 평활하고, 단계는 올라갈 때는 바로, 내려갈 때는 3프레임 연속으로 확인된 뒤 한 단계씩 바꾼다. 다가오는 물체는 빨리 알리고 멀어지는 변화는 확실할 때만 알리는 비대칭 설계이다.

보조 기능으로, YOLO26n[25]이 검출한 위험 물체(입력 512 × 288, 신뢰도 0.40 이상, 자동차·자전거 등 위험도 3, 사람·의자 등 2, 신호등·화분 등 1)가 4 m 이내에 있는 칸의 핀을 위험도에 따라 1°, 2°, 3°씩 초당 10회 떨게 한다. 진동은 서보 위치 지령으로 만들어 핀 갱신 박자(0.2초)의 둘째와 넷째 4분의 1 구간에 핀을 비켜 놓는 방식이므로, 그 주파수(10 Hz)는 손의 진동 감각이 가장 예민한 주파수(수백 Hz)보다 훨씬 낮다[26]. 이 기능은 처리 시간(3.1)에는 포함되지만 이번 연구의 평가 대상은 아니다.

촉각 패드([그림 2])는 4행 × 6열, 24개 핀이며 핀 간격은 가로 30 mm, 세로 40 mm, 외형은 가로 200.0 × 세로 173.0 × 높이 62.3 mm(설계 파일 기준)이다. 왼쪽 3열은 왼손, 오른쪽 3열은 오른손 손바닥이 맡고, 칸의 위치는 화면 위치와 그대로 대응한다. 핀 하나는 SG90 서보와 3D 프린팅한 12잇수 피니언(피치원 지름 16.00 mm)·랙으로 움직이며, PCA9685 PWM 드라이버[27] 두 개가 서보를 12개씩 맡는다. 구동 범위는 140 tick(핀 높이 0~9.0 mm, 보정 전 기준 232~372 tick)이며, 한 단계는 20 tick, 1.29 mm이다. 단계 0의 위치는 핀마다 따로 보정하였다(2.3 (4)). Jetson은 결과가 나올 때마다 31바이트 프레임(CRC-8 검사)을 USB로 제어부인 Raspberry Pi Pico 호환 RP2040 보드[28]에 보내고, 제어부는 0.2초 박자마다 최신 값을 목표로 정해 5 ms마다 최대 4 tick씩 서보를 옮긴다. 유효한 프레임이 0.5초 동안 없으면 모든 핀을 10 ms에 1 tick씩 천천히 가장 낮은 위치로 내린다. 제어부의 전원 자체가 끊기는 경우는 이 안전 기능의 범위 밖이며, 고찰에서 한계로 다룬다. 서보 전원은 3셀 리튬폴리머 배터리 두 개에서 강압 컨버터를 거쳐 드라이버마다 따로 공급하였다. 주요 설정값은 [표 1]과 같고, 구현 코드는 [29]에서 공개한다.

![[그림 2] 촉각 패드의 3D 모델(설계 파일). (a) 패드 전체: 베이스판 위에 서보 유닛 24개(4행 × 6열)가 있고, 핀은 반대쪽 평평한 면의 구멍으로 나온다. (b) 핀 구동부: SG90 서보, 브래킷, 12잇수 피니언, 랙(핀)](figures/final/fig_hw_cad.png){width=7.2}

[표 1] 장치 주요 설정값
| 항목 | 값 |
|---|---|
| 카메라 | Logitech C920, 1280 × 720, 30 fps, 초점 고정, 렌즈 높이 약 0.70 m |
| 연산부 | Jetson Orin Nano Super 8 GB, 25 W, TensorRT FP16 |
| 깊이 입력 | 924 × 504 (가운데 1280 × 698에서 축소) |
| 장면 판별 | Places365 ResNet18, 초당 2회, 문턱 0.65 / 0.35, 유지 1.5 s |
| 깊이 추정 | Depth Anything V2 ViT-S — 실내: 미터 모델(Hypersim) − 0.44 m, 실외: 상대 깊이 + 땅 기준 환산(h 0.70 m, f 908 화소) |
| 칸 대표 거리 | 6 × 4칸, 하위 10번째 백분위 |
| 표시 거리 | 0.5 m ~ 실내 8 m / 실외 20 m, 로그 눈금 8단계 |
| 시간 필터 | 접근 0.65 / 후퇴 0.25 평활, 하강은 3프레임 확인 뒤 한 단계씩 |
| 위험 물체(보조) | YOLO26n 512 × 288, 4 m 이내, 진동 1/2/3°, 초당 10회 |
| 핀 | 24개, 간격 30 × 40 mm, 0~9.0 mm, 단계당 1.29 mm, 핀별 영점 보정 |
| 갱신 | 박자 0.2 s, 5 ms마다 최대 4 tick, 통신 끊김 0.5 s 뒤 천천히 하강 |

### 2.3 실험 절차

거리 정확도 실험의 결과를 보고 깊이 추정의 실내 보정값과 실외 방식, 그리고 표시 거리 d<sub>far</sub>(실내 4 → 8 m, 실외 8 → 20 m)를 바꾸었다([표 1]은 바꾼 뒤의 값). 처리 시간은 바꾸기 전 설정(실외 Virtual KITTI 2 모델, 실내 보정 없음)으로 실내에서 측정하였고, 구동 지연은 깊이 추정을 거치지 않는 시험 프로그램으로 측정하였다. 핀 영점 보정(2.3 (4))은 구동 지연을 측정한 뒤에 하였다.

**(1) 소프트웨어 처리 시간.** 장치는 프레임마다 처리 단계별 소요 시간, 카메라 프레임이 Jetson에 들어온 뒤 처리가 시작되기까지의 대기 시간, 24칸의 거리·단계를 기록한다. 카메라부터 핀까지 모두 연결하고 확인 화면을 띄운 채 실내에서 실행한 기록 두 개(모두 7,894프레임)로 단계별 처리 시간과 대기 시간을 구하였다. 또 확인 화면을 띄우지 않고 제어부를 연결하지 않은 채 60초 동안 실행하여 처리율과 Jetson 모듈의 입력 전력(tegrastats의 VDD_IN, 1초 간격)을 측정하였다.

**(2) 거리 정확도.** 장치의 C920을 노트북에 연결하여 같은 초점 설정으로 1280 × 720 무손실 사진을 찍었다. 카메라는 렌즈가 땅에서 약 0.70 m에 오도록 두고 눈대중으로 수평을 맞추었다. 정밀하게 조정하지는 않았으며, 가장 먼 거리(실외 8 m, 실내 4 m)의 사진에서 표적의 화면 위치로 역산한 기울기는 사진별 −1.1~+1.2°였다. 표적은 흰 상자의 앞면(가로 30 × 세로 27 cm)으로, 상자를 손수레에 올려 앞면 가운데가 렌즈 높이 근처에 오도록 렌즈 정면에 두었고, 거리는 렌즈에서 앞면까지 줄자로 재었다. 실외는 산책로와 주차장, 실내는 거실과 주방에서 찍었으며, 실외는 1, 2, 3, 4, 6, 8 m, 실내는 0.5, 1, 1.5, 2, 3, 4 m에서 거리마다 5장씩 모두 120장을 얻었다. 장소를 두 곳씩 둔 것은 한 장소에서 정한 보정값을 다른 장소에 적용해 보기 위해서이다. 사진마다 상자 앞면 영역을 손으로 표시하고, 장치와 같은 전처리를 거친 깊이 지도에서 그 영역을 사방 20 %씩 줄인 안쪽 화소의 중앙값을 그 사진의 추정 거리로 하였다. 깊이 지도는 처음 설계의 실내·실외 미터 단위 모델과 땅 기준 환산으로 모든 사진에 대해 구하였다.

**(3) 반응 시간.** 반응 시간은 Jetson이 카메라 프레임을 받아 제어부로 보내기까지의 대기와 처리 시간((1)에서 측정)과, 보낸 뒤 핀이 움직이기까지의 구동 지연으로 나누어 쟀다. 구동 지연은 깊이 추정 없이 칸 9(위에서 둘째 줄, 왼쪽에서 넷째 칸)의 단계만 0과 7 사이에서 바꾸어 보내는 시험 프로그램으로 쟀다. 프로그램은 평소 장치처럼 초당 15회 프레임을 계속 보내며, 단계를 바꾸는 프레임을 보낸 직후 모니터 창 전체를 흰색(0 → 7, 올림: 가까운 물체가 나타난 경우) 또는 검은색(7 → 0, 내림: 물체가 사라진 경우)으로 바꾸고, 보낸 시각과 화면 갱신 명령이 끝난 시각을 기록한다. 바꾸는 간격은 2.5~3.5초에서 무작위로 정하여 제어부의 0.2초 박자와 어긋나는 위치가 고르게 섞이게 하였다. 장치를 책상에 두고 스마트폰(Galaxy S10 5G)의 슬로 모션(초당 240프레임)으로 모니터와 칸 9의 핀을 한 화면에 담았으며, 한 번의 녹화에서 올림과 내림을 10회씩 하였다. 녹화 3번 가운데 손에 들고 찍어 구도가 움직인 앞의 2번은 빼고, 스마트폰을 고정한 세 번째 녹화만 썼다. 모니터 영역의 밝기가 흰색과 검은색의 중간값을 지나는 순간(앞뒤 프레임 사이 선형 보간)을 화면 전환 시각으로 하고, 영상의 실제 촬영 속도는 이 시각을 프로그램 기록과 직선으로 맞추어 구하였다. 핀은 화면 전환 40프레임 전의 핀 윗부분을 본으로 삼아 프레임마다 정규화 상호상관으로 세로 위치를 찾았고, 옆의 고정 구조물도 같은 방식으로 추적하여 촬영 흔들림을 뺐다. 이동 전후 위치(차이 약 43.5화소, 9.0 mm) 사이의 진행률이 5 %를 넘는 순간을 움직임 시작, 95 %를 넘는 순간을 도착으로 하고, 화면 전환 기준 값에 보낸 시각부터 화면 갱신 명령이 끝나기까지의 시간을 더하여 보낸 시각 기준으로 나타냈다. 고정 구조물이 1화소 넘게 움직였거나(촬영 흔들림) 핀 이동량이 38~50화소를 벗어난 전환은 분석에서 뺐다. 모니터 표시 지연과, 카메라 안에서 영상이 만들어져 Jetson에 도착하기까지의 지연은 재지 못하였으므로 반응 시간은 실제보다 그만큼 짧게 나온다. 측정은 핀 영점 보정 전 설정에서 하였으나, 보정은 영점과 최대 위치를 같은 만큼 옮기므로 핀의 이동 거리와 시간에는 영향이 없다.

**(4) 핀 영점 오차.** 같은 지령에서 24개 핀의 높이가 조립 공차 때문에 얼마나 다른지를 소프트웨어 영점 보정의 보정량으로 구하였다. 보정 전에는 24핀 모두 단계 0이 372 tick, 단계 7이 232 tick이었다. 모든 핀을 단계 0에 두고, 전용 프로그램에서 핀을 하나씩 골라 핀 윗면이 패드 표면과 같아질 때까지 단계 0의 tick을 옮겼다(한 번에 1 또는 5 tick, 1 tick은 약 0.065 mm). 단계 7의 tick도 같은 수만큼 옮겨 스트로크(140 tick, 9.0 mm)는 유지하였다. 높이가 같은지는 눈과 손끝으로 판단하였고, 보정 범위는 보정 전 값에서 ±80 tick(약 5.2 mm)으로 제한하였다. 보정량(tick)에 tick당 높이를 곱한 값을 그 핀의 보정 전 영점 오차로 하였으며, 보정에서 핀을 내린 경우(보정 전에 패드 표면보다 높았던 경우)를 양수로 하였다. 보정 뒤 남은 오차는 따로 재지 않았다. 보정값은 장치의 보정 파일과 제어부 펌웨어의 기동 기본값에 함께 넣어, Jetson이 연결되기 전 기동 때에도 쓰이게 하였다.

### 2.4 분석 및 통계

처리 시간과 구동 지연은 평균, 표준편차, 중앙값, 범위, 95번째 백분위로 나타냈다. 두 측정은 따로 하였으므로, 설계 요구(시작 0.5초, 도달 1초 이내)는 구동 지연의 시행마다 대기와 처리 시간을 합한 값의 95번째 백분위를 더하여 판단하고, 만족한 시행의 비율을 구하였다. 거리 정확도는 사진마다 상대 오차 (추정 거리 − 실제 거리) / 실제 거리 × 100 %를 구하고, 그 절댓값의 평균(MAPE)을 장소·방법·거리별로 정리하였다. 처음 설계의 미터 단위 모델에는 곱하기(원점을 지나는 최소제곱 배율), 더하기(평균 차이), 1차식, 거듭제곱 보정을 적용하되, 보정값은 한 장소의 사진으로 정해 다른 장소의 사진에 적용(장소 교차)하였다. 땅 기준 환산은 표적 거리를 쓰지 않으므로 모든 사진에 그대로 적용하였다. 표시 단계는 [표 1]의 매핑(시간 필터 제외)으로 실제 거리와 추정 거리를 각각 단계로 바꾸어 일치율과 ±1단계 이내 비율을 구하였다(d<sub>far</sub>는 실내 사진 8 m, 실외 사진 20 m). 같은 거리에서 연달아 찍은 5장은 서로 독립이 아니므로, 두 방법의 비교는 장소 × 거리 묶음(12개)별 평균 오차를 단위로 정확 윌콕슨 부호순위 검정과 묶음 부트스트랩(10,000회) 95 % 신뢰구간으로 하였다. 분석 값은 장치 코드(TensorRT FP16)로 다시 계산하여 확인하였다(사진별 차이 최대 1.3 %). 핀 영점 오차는 평균, 표준편차, 절댓값의 평균과 중앙값, 범위로 나타내고 한 단계 높이(1.29 mm)와 비교하였다. 분석은 Python(NumPy, SciPy)으로 하였고 유의수준은 0.05로 하였다.

## Ⅲ. 결  과

### 3.1 소프트웨어 처리 시간

실내 실행 기록 7,894프레임에서 한 프레임의 처리 시간(처리 시작부터 제어부로 보내기까지)은 평균 68.8 ms, 중앙값 65.5 ms, 95번째 백분위 82.4 ms였다([표 2]). 깊이 추정이 평균 48.5 ms로 가장 길었고, 위험 물체 검출이 14.7 ms였다. 장면 판별은 전체 프레임의 21.3 %(1,680프레임)에서 실행되었고, 그 프레임에서 평균 20.4 ms가 더해졌다. 필터·매핑과 USB 전송은 합쳐서 1.1 ms였다. 카메라 프레임이 Jetson에 들어온 뒤 처리가 시작되기까지의 대기는 평균 34.8 ms였으며, 대기와 처리를 합한 시간은 프레임별로 평균 103.6 ms, 95번째 백분위 137.4 ms, 최대 166.7 ms였다.

확인 화면 없이 60초 동안 실행했을 때는 918프레임을 처리하여 초당 15.3프레임이었고, 처리 시간은 중앙값 64.1 ms, 95번째 백분위 85.9 ms였다. 이때 Jetson 모듈의 입력 전력은 중앙값 14.4 W, 최대 15.1 W였다. 이 측정들은 깊이 추정을 바꾸기 전 설정에서 한 것이며(2.3), 바꾼 뒤 깊이 추정만 따로 잰 시간(30회 예열 뒤 최솟값)은 실내 39.6 ms, 실외 40.6 ms로 바꾸기 전 실내 39.5 ms와 1.1 ms 이내였다.

[표 2] 소프트웨어 단계별 처리 시간 (실내 실행 기록 7,894프레임, ms)
| 단계 | 평균 | 표준편차 | 중앙값 | 95 백분위 | 최대 |
|---|---|---|---|---|---|
| 대기 | 34.8 | 15.5 | 32.5 | 70.1 | 87.3 |
| 깊이 추정 | 48.5 | 3.4 | 48.2 | 55.2 | 78.5 |
| 위험 물체 검출 | 14.7 | 1.4 | 15.1 | 16.3 | 21.9 |
| 장면 판별 | 20.4 | 2.1 | 21.0 | 22.4 | 50.1 |
| 필터·매핑 | 0.5 | 0.1 | 0.5 | 0.7 | 3.1 |
| USB 전송 | 0.6 | 0.4 | 0.6 | 0.7 | 9.5 |
| 처리 | 68.8 | 7.3 | 65.5 | 82.4 | 114.4 |
| 대기 + 처리 | 103.6 | 16.6 | 101.5 | 137.4 | 166.7 |

주: 대기 = Jetson이 프레임을 받은 뒤 처리가 시작되기까지. 깊이 추정은 실내 모델, 위험 물체 검출은 YOLO26n, 장면 판별은 실행한 1,680프레임의 값이다. 처리는 처리 시작부터 보내기까지 그 밖의 처리를 모두 포함한 프레임 전체 시간이며, 확인 화면을 그리는 시간은 들어 있지 않다.

### 3.2 거리 정확도

방법별 오차와 표시 단계 일치율은 [표 3], 거리별 추정 거리는 [그림 3]과 같다.

실내 사진에서 실내 모델은 모든 거리에서 실제보다 멀게 추정하였다(장소 합침 평균 0.5 m → 0.94 m, 1 m → 1.37 m, 4 m → 4.43 m). 거리별 평균 차이는 0.37~0.51 m로 거리에 따라 크게 변하지 않았으며, 전체 평균은 거실 0.47 m, 주방 0.41 m, 합쳐서 0.44 m였다. 다른 장소의 평균 차이를 빼서 보정하면 MAPE는 34.3 %에서 9.5 %가 되었고, 곱하기 보정은 18.0 %, 1차식과 거듭제곱 보정은 각각 9.4 %, 9.6 %였다.

실외 사진에서 실외 모델은 1 m를 평균 8.82 m, 8 m를 27.28 m로 추정하였다(장소 합침). 곱하기 배율은 산책로 0.257, 주차장 0.157이었고, 장소 교차 보정 후 MAPE는 곱하기 63.2 %, 다른 보정 70.2~172.0 %였다. 같은 사진에서 실내 모델 − 0.44 m의 MAPE는 38.0 %(산책로 6.7 %, 주차장 69.3 %), 땅 기준 환산은 21.1 %(산책로 10.9 %, 주차장 31.2 %)였다. 땅 기준 환산은 주차장 사진 30장을 모두 실제보다 멀게 추정하였고(평균 상대 오차 +31.2 %, 1 m → 1.41 m, 8 m → 10.38 m), 산책로의 평균 상대 오차는 +3.3 %였다. 땅 기준 환산의 오차는 실내 모델 − 0.44 m보다 묶음 평균 16.9 %p 작았고(95 % 신뢰구간 −32.1 ~ −2.9 %p), 12묶음 중 7개에서 작았다(윌콕슨 p = 0.092). 땅 기준 환산을 실내 사진에 적용하면 MAPE는 54.8 %였고, 4 m 표적을 장소별 평균 9.24 m(거실), 7.55 m(주방)로 추정하였다.

화면 아래쪽 땅(기하 거리 1.82~3.5 m)에서 모델 깊이와 기하 거리의 비(장소별 사진 중앙값)는 실외 모델이 산책로 3.69, 주차장 3.38, 거실 3.14, 주방 3.11이었고, 실내 모델은 각각 1.24, 1.30, 1.02, 0.88이었다. 가정한 카메라 기울기가 실제와 1° 다르면 땅 기준 환산의 실외 MAPE는 16.8~26.3 %, 3° 다르면 12.6~41.3 %였고, 가정한 높이가 5 cm 다르면 16.1~27.3 %, 10 cm 다르면 13.5~34.9 %였다. 카메라가 실제로는 3° 위를 보았다고 가정하면 주차장 사진의 MAPE는 12.6 %였다.

[표 3] 거리 정확도 — 방법별 MAPE와 표시 단계 일치율 (%)
| 방법 | 장소 1 | 장소 2 | 전체 | 단계 일치 | ±1단계 |
|---|---|---|---|---|---|
| § 실내 사진 (장소 1 거실, 장소 2 주방, 단계는 d<sub>far</sub> 8 m 기준) |
| 실내 모델 | 34.6 | 34.0 | 34.3 | 60 | 92 |
| 실내 모델 × 배율 (장소 교차) | 17.8 | 18.3 | 18.0 | 70 | 98 |
| 실내 모델 − 차이 (장소 교차) | 10.5 | 8.5 | 9.5 | 75 | 100 |
| § 실외 사진 (장소 1 산책로, 장소 2 주차장, 단계는 d<sub>far</sub> 20 m 기준) |
| 실외 모델 | 447.2 | 589.8 | 518.5 | 0 | 0 |
| 실외 모델 × 배율 (장소 교차) | 48.1 | 78.2 | 63.2 | 25 | 80 |
| 실내 모델 − 0.44 m | 6.7 | 69.3 | 38.0 | 55 | 92 |
| 땅 기준 환산 | 10.9 | 31.2 | 21.1 | 60 | 100 |

주: 장소마다 사진 30장. 장소 교차는 그 장소의 사진에 다른 장소의 사진으로 정한 보정값을 적용한 결과이다.

![[그림 3] 줄자 거리와 추정 거리(로그 눈금). (a) 실내 사진: 실내 모델 보정 전과, 다른 장소의 평균 차이로 보정한 값. (b) 실외 사진: 실외 모델 보정 전과 땅 기준 환산. 점은 같은 거리 5장의 평균, 막대는 표준편차, 점선은 추정 = 실제](figures/kiro_C/fig_C3_distance.png){width=6.8}

### 3.3 반응 시간

세 번째 녹화의 전환 20회 가운데 고정 구조물이 1화소 넘게 움직인 2회(올림)와 핀 이동량이 60화소로 범위를 벗어난 1회(내림)를 빼고 17회(올림 8회, 내림 9회)를 분석하였다. 영상의 실제 촬영 속도는 초당 235.05프레임이었고, 화면 전환 시각을 프로그램 기록에 맞춘 잔차는 표준편차 17.7 ms(절댓값 최대 31.7 ms)였다. 보낸 시각부터 화면 갱신 명령이 끝나기까지는 평균 27.2 ms(26.4~28.7 ms)였다.

Jetson이 보낸 뒤 핀이 움직이기 시작하기까지는 평균 116.3 ms(41.6~215.7 ms), 도착하기까지는 평균 280.1 ms(190.1~379.2 ms)였다([표 4], [그림 4]). 움직이기 시작해서 도착하기까지는 평균 163.8 ms(표준편차 6.8 ms, 148.5~175.2 ms)였다. 도착 시간의 평균은 올림 296.6 ms, 내림 265.4 ms였다.

3.1의 대기와 처리를 합한 시간의 평균(103.6 ms)을 더하면 반응 시간은 시작 평균 약 220 ms, 도착 평균 약 384 ms이다. 그 95번째 백분위(137.4 ms)를 더하면 시작은 최대 353.1 ms, 도착은 최대 516.6 ms로 17회 모두 설계 요구(시작 0.5초, 도달 1초 이내)를 만족하였고, 최댓값(166.7 ms)을 더해도 시작은 최대 382.4 ms, 도착은 최대 545.9 ms였다.

[표 4] 구동 지연 — Jetson이 보낸 뒤 핀이 움직이기까지 (ms)
| 구간 | 평균 ± 표준편차 | 범위 | 95 백분위 |
|---|---|---|---|
| 보냄 → 시작 | 116.3 ± 54.2 | 41.6~215.7 | 205.9 |
| 보냄 → 도착 | 280.1 ± 55.8 | 190.1~379.2 | 375.6 |
| 시작 → 도착 | 163.8 ± 6.8 | 148.5~175.2 | 174.6 |

주: 17회(올림 8회, 내림 9회). 시작 = 이동 거리(9.0 mm)의 5 %, 도착 = 95 %. 중앙값은 차례로 108.7, 275.8, 163.5 ms, 올림 / 내림 평균은 차례로 130.0 / 104.1, 296.6 / 265.4, 166.6 / 161.4 ms이다. 모니터 표시 지연은 빠져 있다(2.3 (3)).

![[그림 4] 시행별 구동 지연. 선 하나가 시행 하나이며, 동그라미는 움직임 시작, 네모는 도착, 점선은 Jetson이 보낸 시각이다. 위의 화살표는 시작 시각이 퍼진 폭이다](figures/kiro_C/fig_C4_latency.png){width=7.2}

### 3.4 핀 영점 오차

보정 전 24개 핀의 영점 오차는 평균 0.00 mm, 표준편차 2.20 mm, 절댓값의 평균 1.61 mm(중앙값 1.29 mm), 범위 −3.55 ~ +5.17 mm였다([표 5]). 보정이 필요 없던 핀은 5개였고, 8개는 패드 표면보다 높았으며 11개는 낮았다. 오차가 한 단계(20 tick, 1.29 mm) 이하인 핀은 13개(보정이 필요 없던 5개 포함), 두 단계를 넘는 핀은 7개였고, 가장 큰 오차는 네 단계에 해당하였다. 칸 5는 보정 범위의 끝(80 tick)까지 옮겼으므로 실제 오차는 5.17 mm보다 클 수 있다.

[표 5] 핀별 보정 전 영점 오차 (mm)
| 행 | 1열 | 2열 | 3열 | 4열 | 5열 | 6열 |
|---|---|---|---|---|---|---|
| 1 | +3.23 | +0.65 | 0.00 | −1.94 | +1.61 | +5.17 |
| 2 | 0.00 | −0.32 | −0.97 | −3.55 | 0.00 | +1.29 |
| 3 | −3.23 | −0.65 | −0.97 | −2.58 | −3.23 | 0.00 |
| 4 | 0.00 | +1.29 | −0.32 | −1.61 | +2.91 | +3.23 |

주: 칸 배치는 화면과 같다(1~3열 왼손, 4~6열 오른손). + = 보정 전 패드 표면보다 높음. 칸 5(1행 6열)는 보정 범위의 끝까지 옮긴 값이다.

## Ⅳ. 고  찰

### 4.1 거리 추정

처음 설계의 실외 미터 모델은 보행 높이에서 찍은 사진의 거리를 여러 배 멀게 추정하였고, 같은 경향이 실내 사진의 바닥에서도 나타났다(땅 거리 비 3.11~3.69). Virtual KITTI 2는 KITTI 주행 영상을 가상으로 재현한 자료이므로[22], 학습 카메라는 KITTI처럼 땅에서 약 1.65 m 높이의 차량에 달려 있다고 볼 수 있다[30]. 이 높이와 학습 영상의 화각(초점거리 ÷ 영상 높이)을 가정하여 장치 카메라(높이 0.70 m, 초점거리 908 화소)와 비교하면 배율이 약 3.5배로 계산되어, 측정한 땅 거리 비와 비슷하다. 즉 실외 모델의 큰 오차는 장면보다 학습 카메라와 장치 카메라의 높이·초점거리 차이로 대부분 설명될 수 있으며, 한 장의 영상에서 얻는 미터 단위 깊이에 촬영 카메라의 조건이 그대로 들어간다는 지적과 맞는다[15]. 그런데 이 모델의 곱하기 배율은 장소마다 0.257, 0.157로 달라, 한 장소에서 정한 보정은 다른 장소에서 63.2 %의 오차를 남겼다.

땅 기준 환산은 표적 거리 없이 장치의 카메라 높이와 초점거리만으로 배율을 정하므로 장소마다 따로 맞출 값이 없고, 두 실외 장소 모두에서 표시 단계가 ±1단계 안에서 일치하였다. 차량의 단안 영상에서 카메라 높이로 배율을 정하던 방법[23, 24]이 보행 높이의 착용형 카메라와 한 장의 상대 깊이 지도에서도 쓰일 수 있음을 보여 준다. 실내 모델 − 0.44 m는 산책로에서 6.7 %로 오히려 정확하였으나 주차장에서는 69.3 %로, 장소에 따른 차이가 더 컸다. 다만 묶음 비교의 부트스트랩 신뢰구간은 0을 포함하지 않았지만 윌콕슨 검정은 유의하지 않았고(p = 0.092), 12묶음이 두 장소에서 나왔으므로 장소 사이의 차이까지 반영한 결론으로 보기는 어렵다.

땅 기준 환산에 남은 오차는 주로 주차장에서 나왔고, 30장 모두 멀게 추정된 체계적인 오차였다. 카메라가 실제로 3° 위를 보았다고 가정하면 주차장의 오차는 12.6 %로 줄었으나, 표적 위치로 역산한 기울기는 −1.1~+1.2°였으므로 기울기만으로는 설명이 충분하지 않다. 화면 아래쪽 땅의 경사나 렌즈 높이의 차이도 원인일 수 있으나 이 자료로는 구분할 수 없다. 기울기 가정이 1° 틀리면 MAPE가 약 4~5 %p 변하였으므로 걸을 때 계속 바뀌는 카메라 기울기가 가장 큰 오차 요인이 될 것이며, 관성 센서로 기울기를 재어 넣거나 깊이 지도에서 땅 평면을 직접 찾는 방법을 검토할 필요가 있다. 실내에서는 가까운 상자가 화면 아래쪽 바닥을 가리는 등 땅 기준 환산이 맞지 않았으므로(MAPE 54.8 %), 장면 판별로 두 방법을 나누어 쓰는 구성이 필요하다.

실내 모델의 오차는 거리와 거의 관계없는 더하기 꼴이어서 곱하기 보정(18.0 %)보다 평균 차이를 빼는 보정(9.5 %)이 잘 맞았으나, 원인은 확인하지 못하였다. 또 이 값은 세운 상자로 정하였으므로 바닥에는 맞지 않을 수 있다. 실내 모델은 바닥을 기하 거리의 0.88~1.02배로 추정하였으므로, 0.44 m를 빼면 화면 맨 아래의 바닥(기하 거리 1.82 m)이 약 1.2~1.4 m로 표시된다. 바닥만 보이는 맨 아래 칸의 대표 거리(계산 약 1.92 m, 단계 4)도 1.25~1.52 m가 되어 실내 눈금의 단계 4와 5의 경계(약 1.35 m)에 걸치므로, 장소에 따라 바닥 줄의 핀이 한 단계 높게 표시될 수 있다. 걷는 기준인 바닥의 표시 높이가 실내와 실외에서 달라지지 않도록, 바닥 줄에는 보정을 달리 적용하는 방법을 검토할 필요가 있다.

### 4.2 반응 시간

구동 지연의 시작 시간은 41.6~215.7 ms로 퍼진 폭이 174 ms였으나, 움직이기 시작해서 도착하기까지는 163.8 ± 6.8 ms로 거의 일정하였다([그림 4]). 시작 시간의 폭은 제어부가 0.2초 박자마다 새 값을 적용하는 구조와 맞는다. 바꾸는 간격을 무작위로 두었으므로 보낸 시각부터 다음 박자까지의 대기는 0~200 ms에 고르게 퍼지고 평균 약 100 ms로 예상되며, 이것이 시작 시간 평균 116.3 ms의 대부분을 차지한다. 이동 시간은 펌웨어의 속도 제한(5 ms마다 4 tick)으로 계산한 5~95 % 구간 시간 157.5 ms보다 약간 길었다. 따라서 구동 지연은 서보의 성능보다 박자와 속도 제한이라는 펌웨어 설정이 주로 정한다. 박자를 줄이면 시작이 빨라지지만, 한 박자 안에 끝에서 끝까지 움직이도록 정한 구동 범위와 함께 다시 정해야 한다. 같은 이유로 핀의 갱신은 Jetson의 처리율(초당 15.3프레임)과 관계없이 초당 5회이다.

처리와 구동을 합한 반응 시간은 가장 늦은 시행에서도 시작 353.1 ms, 도착 516.6 ms로 요구 안이었다. 그러나 카메라 안에서 영상이 만들어져 Jetson에 도착하기까지의 지연과 모니터 표시 지연은 재지 못했으므로, 실제 반응 시간은 그만큼 길다. 두 지연의 합이 시작 요구까지 남은 약 147 ms를 넘으면 가장 늦은 경우에 요구를 넘을 수 있으므로, 장면 변화부터 핀 움직임까지를 한 번에 재는 측정이 필요하다. 또 측정은 핀 하나(칸 9)와 녹화 한 번의 17회로 하였고, 화면 전환 시각의 잔차가 표준편차 17.7 ms였으므로 시행 하나의 값에는 수십 ms의 불확실성이 있다. 24개 핀이 함께 움직일 때의 전류와 그에 따른 속도 변화도 재지 않았다.

### 4.3 핀 영점

보정 전 영점 오차는 표준편차 2.20 mm로 한 단계(1.29 mm)보다 컸고, 24개 중 11개가 한 단계를 넘었으며 가장 큰 오차는 네 단계였다. 보정하지 않으면 단계 0인 핀이 많게는 2~4단계 높이만큼 튀어나와 가까운 물체로 읽힐 수 있으므로, 8단계 표시에서는 핀별 영점 보정이 필수적이다. 오차의 절댓값이 3 mm를 넘은 6개 핀(3.23~5.17 mm)은 피니언 이 하나의 간격(원주 피치 약 4.19 mm, 약 65 tick)과 비슷하여, 조립 때 랙과 피니언이 이 하나만큼 어긋나게 맞물렸을 가능성이 있으나 확인하지 않았다. 조립할 때 맞물림 위치를 표시하거나 지그를 쓰면 이런 큰 오차를 줄일 수 있을 것이다. 소프트웨어 보정은 기구를 다시 조립하지 않고 오차를 흡수하였지만, 칸 5는 보정 범위의 끝(+80 tick)에 걸려 아직 패드 표면보다 높을 수 있다. 보정 뒤 남은 오차는 눈과 손끝으로 판단하였고 조정 걸음이 대부분 5 tick(약 0.32 mm)이었으나 따로 재지 않았으므로, 캘리퍼스 같은 도구로 확인해야 한다. 또 한 단계 1.29 mm가 손바닥에서 구별되는지 재지 않았으므로, 8단계가 모두 구별되는지는 높이 변별 실험으로 확인해야 한다.

### 4.4 한계와 후속 연구

거리 정확도는 실내·실외 각 두 장소에서 같은 상자 표적을 렌즈 정면에 두고 찍은 정지 사진으로만 평가하였고, 실외 8 m, 실내 4 m까지만 확인하였으므로 그보다 먼 표시 범위(실외 20 m, 실내 8 m)의 정확도는 알 수 없다. 평가는 표적 영역의 중앙값으로 하였으며, 장치가 쓰는 칸의 하위 10번째 백분위와 표적 영역 값의 비는 처음 설계의 미터 모델에서 중앙값 0.98(실내), 0.96(실외)으로 1에 가까웠으나 바꾼 방법에서는 확인하지 않았다. 걸을 때의 카메라 높이·기울기 변화와 영상 흐림, 땅 기준 환산의 배율 평활 효과, 장면 판별의 정확도도 검증하지 않았다. 또 카메라를 0.70 m 높이에 수평으로 달면 세로 반화각이 약 21°이므로, 발 앞 약 1.8 m 안의 땅과 1 m 앞에서 높이 약 32 cm 아래의 물체는 화면에 들어오지 않는다. 이 영역은 흰지팡이가 맡는 범위이므로, 이 장치는 흰지팡이를 대신하기보다 그 위쪽과 먼 곳을 보완하는 용도로 보아야 한다.

안전 기능은 통신이 끊기면 핀을 천천히 내리지만, 제어부의 전원이 끊기면 서보가 힘을 잃어 핀의 위치를 제어할 수 없다. 핀을 기구적으로 되돌리는 구조나 전원 감시가 필요하다. 위험 물체 진동은 처리 시간에만 포함되었고, 1° 진동이 서보의 불감대 안에 들어 실제로 움직이지 않을 가능성을 포함하여 평가하지 않았다. 배터리로 쓸 수 있는 시간도 재지 않았다.

가장 큰 한계는 사람이 장치를 쓰는 평가가 없다는 점이다. 연구자 1인이 눈을 가리고 장애물이 놓인 10 m 복도를 흰지팡이, 장치, 둘 다를 써서 걷는 예비 시험과, 장애물 앞 1~4 m에서 표시 단계를 기록하는 정지 감지 시험을 계획하였으나 수행하지 못하였다. 후속 연구에서는 이 두 시험을 먼저 하고, 높이 변별 실험으로 단계 수를 정한 뒤, 연구윤리 심의를 거쳐 여러 참여자와 시각장애 당사자의 평가로 넓혀야 한다.

## Ⅴ. 결  론

본 연구는 일반 카메라 한 대와 범용 부품으로 앞쪽 거리를 양 손바닥 아래 24개 핀의 높이로 전달하는 장치를 구현하고, 정지 사진과 장치 기록으로 평가하였다. 실내에서는 실내 미터 모델에서 0.44 m를 빼는 보정으로 장소 교차 MAPE 9.5 %, 실외에서는 상대 깊이의 땅 기준 환산으로 MAPE 21.1 %를 얻었고, 두 경우 모두 표시 단계가 ±1단계 안에서 일치하였다. 처리와 구동을 합한 반응 시간은 17회 모두 설계 요구(시작 0.5초, 도달 1초) 안이었고, 시작 시간의 흩어짐은 제어부의 0.2초 박자 대기로 설명되었다. 핀 영점 오차는 최대 네 단계에 이르러 핀별 보정이 필요하였다. 걸을 때의 정확도와 보행 보조 효과는 보행 시험으로 확인해야 한다.

## 참고문헌

[1] World Health Organization, “Blindness and vision impairment,” Fact sheet, Feb. 2026. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/blindness-and-visual-impairment

[2] GBD 2019 Blindness and Vision Impairment Collaborators and Vision Loss Expert Group of the Global Burden of Disease Study, “Trends in prevalence of blindness and distance and near vision impairment over 30 years: an analysis for the Global Burden of Disease Study,” The Lancet Global Health, vol. 9, no. 2, pp. e130–e143, 2021. https://doi.org/10.1016/S2214-109X(20)30425-3

[3] 보건복지부, “2023년 등록장애인 현황,” 2024년 4월 18일 발표. 보도: J. Lee, “5.1% of Korean population registered as disabled in 2023: report,” The Korea Herald, Apr. 18, 2024. [Online]. Available: https://www.koreaherald.com/article/3373945

[4] R. Manduchi and S. Kurniawan, “Mobility-related accidents experienced by people with visual impairment,” Insight: Research and Practice in Visual Impairment and Blindness, vol. 4, no. 2, 2011.

[5] P. Bach-y-Rita, C. C. Collins, F. A. Saunders, B. White, and L. Scadden, “Vision substitution by tactile image projection,” Nature, vol. 221, no. 5184, pp. 963–964, 1969. https://doi.org/10.1038/221963a0

[6] N. Sadato, A. Pascual-Leone, J. Grafman, V. Ibañez, M.-P. Deiber, G. Dold, and M. Hallett, “Activation of the primary visual cortex by Braille reading in blind subjects,” Nature, vol. 380, no. 6574, pp. 526–528, 1996. https://doi.org/10.1038/380526a0

[7] M. Ptito, S. M. Moesgaard, A. Gjedde, and R. Kupers, “Cross-modal plasticity revealed by electrotactile stimulation of the tongue in the congenitally blind,” Brain, vol. 128, no. 3, pp. 606–614, 2005. https://doi.org/10.1093/brain/awh380

[8] U.S. Food and Drug Administration, “De Novo classification request for BrainPort V100 (DEN130039),” decision date Jun. 18, 2015. [Online]. Available: https://www.accessdata.fda.gov/scripts/cdrh/cfdocs/cfpmn/denovo.cfm?id=DEN130039

[9] P. Grant, L. Spencer, A. Arnoldussen, R. Hogle, A. Nau, J. Szlyk, J. Nussdorf, D. C. Fletcher, K. Gordon, and W. Seiple, “The functional performance of the BrainPort V100 device in persons who are profoundly blind,” Journal of Visual Impairment & Blindness, vol. 110, no. 2, pp. 77–88, 2016. https://doi.org/10.1177/0145482X1611000202

[10] P. B. L. Meijer, “An experimental system for auditory image representations,” IEEE Transactions on Biomedical Engineering, vol. 39, no. 2, pp. 112–121, 1992. https://doi.org/10.1109/10.121642

[11] D. Dakopoulos and N. G. Bourbakis, “Wearable obstacle avoidance electronic travel aids for blind: a survey,” IEEE Transactions on Systems, Man, and Cybernetics, Part C (Applications and Reviews), vol. 40, no. 1, pp. 25–35, 2010. https://doi.org/10.1109/TSMCC.2009.2021255

[12] W. Elmannai and K. Elleithy, “Sensor-based assistive devices for visually-impaired people: current status, challenges, and future directions,” Sensors, vol. 17, no. 3, art. 565, 2017. https://doi.org/10.3390/s17030565

[13] R. K. Katzschmann, B. Araki, and D. Rus, “Safe local navigation for visually impaired users with a time-of-flight and haptic feedback device,” IEEE Transactions on Neural Systems and Rehabilitation Engineering, vol. 26, no. 3, pp. 583–593, 2018. https://doi.org/10.1109/TNSRE.2018.2800665

[14] F. Vidal-Verdú and M. Hafez, “Graphical tactile displays for visually-impaired people,” IEEE Transactions on Neural Systems and Rehabilitation Engineering, vol. 15, no. 1, pp. 119–130, 2007. https://doi.org/10.1109/TNSRE.2007.891375

[15] W. Yin, C. Zhang, H. Chen, Z. Cai, G. Yu, K. Wang, X. Chen, and C. Shen, “Metric3D: Towards zero-shot metric 3D prediction from a single image,” in Proc. IEEE/CVF International Conference on Computer Vision (ICCV), 2023, pp. 9009–9019. https://doi.org/10.1109/ICCV51070.2023.00830

[16] L. Yang, B. Kang, Z. Huang, Z. Zhao, X. Xu, J. Feng, and H. Zhao, “Depth Anything V2,” in Advances in Neural Information Processing Systems 37 (NeurIPS 2024), 2024, pp. 21875–21911. https://doi.org/10.52202/079017-0688

[17] Logitech, “C920 technical specifications,” Logitech Support. [Online]. Available: https://support.logi.com/hc/en-us/articles/360023307294-C920-Technical-Specifications

[18] B. Zhou, A. Lapedriza, A. Khosla, A. Oliva, and A. Torralba, “Places: A 10 million image database for scene recognition,” IEEE Transactions on Pattern Analysis and Machine Intelligence, vol. 40, no. 6, pp. 1452–1464, 2018. https://doi.org/10.1109/TPAMI.2017.2723009

[19] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image recognition,” in Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016, pp. 770–778. https://doi.org/10.1109/CVPR.2016.90

[20] CSAILVision, “Places365: The Places365-CNNs for scene classification,” GitHub repository. [Online]. Available: https://github.com/CSAILVision/places365

[21] M. Roberts, J. Ramapuram, A. Ranjan, A. Kumar, M. A. Bautista, N. Paczan, R. Webb, and J. M. Susskind, “Hypersim: A photorealistic synthetic dataset for holistic indoor scene understanding,” in Proc. IEEE/CVF International Conference on Computer Vision (ICCV), 2021, pp. 10892–10902. https://doi.org/10.1109/ICCV48922.2021.01073

[22] Y. Cabon, N. Murray, and M. Humenberger, “Virtual KITTI 2,” arXiv:2001.10773, 2020. https://doi.org/10.48550/arXiv.2001.10773

[23] S. Song and M. Chandraker, “Robust scale estimation in real-time monocular SFM for autonomous driving,” in Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2014, pp. 1566–1573. https://doi.org/10.1109/CVPR.2014.203

[24] D. Zhou, Y. Dai, and H. Li, “Ground-plane-based absolute scale estimation for monocular visual odometry,” IEEE Transactions on Intelligent Transportation Systems, vol. 21, no. 2, pp. 791–802, 2020. https://doi.org/10.1109/TITS.2019.2900330

[25] Ultralytics, “Ultralytics YOLO26,” Ultralytics documentation. [Online]. Available: https://docs.ultralytics.com/models/yolo26/

[26] K. O. Johnson, “The roles and functions of cutaneous mechanoreceptors,” Current Opinion in Neurobiology, vol. 11, no. 4, pp. 455–461, 2001. https://doi.org/10.1016/S0959-4388(00)00234-8

[27] NXP Semiconductors, “PCA9685: 16-channel, 12-bit PWM Fm+ I²C-bus LED controller,” Product data sheet, Rev. 4, Apr. 2015.

[28] Raspberry Pi Ltd, “RP2040 datasheet: A microcontroller by Raspberry Pi,” 2025. [Online]. Available: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf

[29] 오형준, “tactile-vision: 시각-촉각 감각 대체 장치,” GitHub 저장소, 커밋 〔최종 원고 때 확정〕, 2026. [Online]. Available: https://github.com/MuakTiger/tactile-vision

[30] A. Geiger, P. Lenz, C. Stiller, and R. Urtasun, “Vision meets robotics: The KITTI dataset,” The International Journal of Robotics Research, vol. 32, no. 11, pp. 1231–1237, 2013. https://doi.org/10.1177/0278364913491297
