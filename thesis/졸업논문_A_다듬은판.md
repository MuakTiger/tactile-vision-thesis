> 작성 메모 (docx에는 들어가지 않음)
>
> 1. A판(다듬은 판, 2026-10-19 iMac): `졸업논문_양식1.md`(10/16~17 젯슨 원고)를 바탕으로 다듬고 Ⅳ 고찰·Ⅴ 결론·요약 결과를 더했다. 원래 원고는 그대로 둔다.
> 2. 정지 감지·1인 보행은 저장소에 자료가 없어(10/17 기준 '아직 안 함') 연구 목적·방법·결과에서 뺐다. 실험을 하면 `졸업논문_양식1.md`의 2.1·2.3 (5)·2.4 문단과 [표 6]·[표 7] 자리를 되살려 3.5로 넣는다.
> 3. 수치 근거: FACTS §1.8~§1.11, `analysis/out_distance/`, `out_latency/`, `out_pin_zero/`, `out_level/`(level_budget.py). 그림은 `analysis/paper_figures.py`가 만든 `figures/final/fig_A*.png`, [그림 2]는 `analysis/hw_figure.py`가 하드웨어 저장소 STL로 만든 `fig_hw_cad.png`(착용형 하우징 STL은 설계만 해서 넣지 않음).
> 4. 〔 〕 = 사용자가 채울 곳(docx에서는 노란색): 영문 이름, [26] 커밋 해시.
> 5. docx 만들기: `python thesis/양식/build_docx.py thesis/졸업논문_A_다듬은판.md`

---
title_ko: 단안 카메라 거리 추정을 이용한 24핀 손바닥 촉각 보행 보조 장치의 구현과 예비 평가
title_en: Implementation and Preliminary Evaluation of a 24-Pin Palm Tactile Walking Aid Using Monocular Camera Distance Estimation
authors_ko: 오형준 · 하지현
authors_en: 〔Hyeong-Jun Oh · Ji-Hyeon Ha〕
---

## 요약

**목적:** 본 연구는 일반 카메라 한 대로 추정한 앞쪽 공간의 방향별 거리를 양 손바닥 아래 24개 핀의 높이로 전달하는 착용형 시각-촉각 보행 보조 장치를 구현하고, 사용자 시험에 앞서 그 기계적·기능적 성능을 평가하는 것을 목적으로 한다. **방법:** NVIDIA Jetson Orin Nano에서 Depth Anything V2로 거리를 추정하였다. 장면 판별 결과에 따라 실내에서는 미터 단위 실내 모델의 출력에서 0.44 m를 빼고, 실외에서는 상대 깊이를 카메라 높이와 화면 속 땅의 위치로 미터로 바꾸었다(땅 기준 환산). 6 × 4칸의 하위 10번째 백분위 거리는 로그 눈금 8단계의 핀 높이(0~9.0 mm)로 바꾸었다. 장치 실행 기록으로 처리 시간을 구하고, 장치 카메라로 네 장소에서 찍은 사진 120장의 추정 거리를 줄자 거리와 비교하였다. Jetson이 핀 지령을 보낸 뒤 핀이 움직이기까지의 구동 지연은 초당 약 240프레임 영상으로 17회 재었고, 24핀의 영점 오차는 핀별 소프트웨어 보정의 보정량으로 구하였다. **결과:** 한 프레임의 처리 시간은 평균 68.8 ms(초당 15.3프레임)였다. 실내 모델은 거리와 거의 무관하게 약 0.44 m 멀게 추정하였고, 다른 장소에서 구한 차이로 보정하면 평균 절대 백분율 오차(MAPE)가 34.3 %에서 9.5 %로 줄었다. 실외 미터 단위 모델의 MAPE는 518.5 %였으나 땅 기준 환산은 21.1 %였고, 보정한 두 방법 모두 모든 사진에서 표시 단계가 실제와 1단계 이내였다. 처리 시간을 더한 반응 시간은 핀 움직임 시작 평균 219.9 ms, 도착 평균 383.7 ms로 17회 모두 설계 요구(시작 0.5초, 도착 1초 이내)를 만족하였다. 보정 전 핀 영점 오차는 표준편차 2.20 mm(−3.55 ~ +5.17 mm)였고, 24핀 중 11개가 한 단계(1.29 mm)를 넘었다. **결론:** 범용 부품으로 만든 장치는 반응 시간 요구를 만족하였으나, 단안 깊이 모델의 거리 배율과 3D 프린팅 기구의 영점은 그대로 쓸 수 없어 장면별 거리 보정과 핀별 소프트웨어 보정이 필요하였다. 사용자가 핀 높이를 구별하여 보행에 활용할 수 있는지는 후속 연구로 확인해야 한다.

**주제어:** 감각 대체, 촉각 디스플레이, 단안 깊이 추정, 시각장애, 보행 보조기기

## Abstract

**Purpose:** This study implements a wearable visual-to-tactile walking aid that conveys the distance of the space ahead, estimated from a single ordinary camera, as the heights of 24 pins under both palms, and evaluates its mechanical and functional performance before user trials. **Methods:** Distance was estimated with Depth Anything V2 on an NVIDIA Jetson Orin Nano. According to a scene classifier, 0.44 m was subtracted from the output of the metric indoor model indoors, and outdoors relative depth was converted to metres using the camera height and the position of the ground in the image (ground-based scaling). The 10th-percentile distance of each of 6 × 4 cells was mapped on a logarithmic scale to eight pin heights (0–9.0 mm). Processing time was obtained from device logs, and distances estimated from 120 photographs taken with the device camera at four sites were compared with tape-measured distances. The actuation latency from command transmission to pin movement was measured 17 times with video at about 240 frames/s, and the zero-level error of the 24 pins was obtained from a per-pin software calibration. **Results:** The mean processing time per frame was 68.8 ms (15.3 frames/s). The indoor model overestimated distance by about 0.44 m almost independently of distance; subtracting the offset obtained at the other site reduced the mean absolute percentage error (MAPE) from 34.3 % to 9.5 %. The metric outdoor model gave a MAPE of 518.5 %, whereas ground-based scaling gave 21.1 %; with both corrected methods every photograph was displayed within one level of the true level. Including processing time, the pin started moving after 219.9 ms and arrived after 383.7 ms on average, and all 17 trials met the design requirement (start within 0.5 s, arrival within 1 s). Before calibration, the zero-level error of the pins had a standard deviation of 2.20 mm (−3.55 to +5.17 mm), and 11 of the 24 pins deviated by more than one level (1.29 mm). **Conclusion:** The device built from general-purpose parts met the latency requirement, but neither the distance scale of the monocular depth models nor the zero level of the 3D-printed mechanism could be used as they were; scene-specific distance correction and per-pin software calibration were necessary. Whether users can discriminate the pin heights and use them while walking remains to be examined in future work.

**Keywords:** sensory substitution, tactile display, monocular depth estimation, visual impairment, mobility aid

## Ⅰ. 서  론

세계보건기구(WHO)는 전 세계에서 적어도 22억 명이 시각 손상을 가지고 있다고 보고하였고[1], 세계질병부담(GBD) 연구는 2020년 기준 실명 인구를 4,330만 명으로 추정하였다[2]. 국내에서도 약 25만 명이 시각장애인으로 등록되어 있다[3]. 시각장애인이 혼자 걸을 때 필요한 것은 앞쪽 공간의 어느 방향이, 어느 높이에서, 얼마나 가까이 막혀 있는지에 대한 정보이다. 흰지팡이는 몸 앞의 바닥 가까운 영역만 알려 주므로, 허리 위로 튀어나온 물체나 머리 높이의 장애물과 부딪히는 사고는 지팡이나 안내견을 쓰는 사람에게도 흔하다[4].

이를 다른 감각으로 보완하려는 시도가 감각 대체(sensory substitution)이다. Bach-y-Rita는 카메라 영상을 등에 놓인 400개의 진동 자극기로 전달하여, 선천성 시각장애인이 훈련 뒤 자극만으로 물체와 그 배치를 구별할 수 있음을 보였다[5]. 이후 시각장애인의 시각 피질이 점자 읽기나 혀 전기 자극 같은 촉각 과제에 쓰인다는 신경가소성 연구가 이를 뒷받침하였다[6, 7]. 혀에 20 × 20 전극을 쓰는 BrainPort는 흰지팡이를 보조하는 기기로 미국 식품의약국(FDA)의 판매 허가를 받았고[8, 9], 영상을 소리로 바꾸는 vOICe도 제안되었다[10].

그러나 기존 전자 보행 보조기기는 대개 한 방향의 거리만 알리거나, 몇 개 방향의 진동처럼 해상도가 낮거나, 소리를 써서 주변 소리를 듣는 데 필요한 청각을 차지하였으며, 사용자 평가와 일상 사용으로 이어진 경우도 드물었다[11–13]. 핀의 높이로 모양을 보여 주는 촉각 디스플레이는 정적인 높이로 정보를 전할 수 있으나 핀마다 구동기가 필요하여 크고 비싸다[14]. 거리를 얻는 방법도 제약이었다. 깊이 카메라는 비싸고 적외선 방식은 햇빛 아래에서 성능이 떨어지며, 일반 카메라 한 대의 깊이 추정은 최근까지 상대적인 앞뒤 순서만 알려 주었다. 최근 공개된 Depth Anything V2는 미터 단위 거리를 직접 출력하는 실내용·실외용 모델을 함께 제공한다[15]. 다만 이런 모델이 보행 높이의 카메라에서 실제로 얼마나 정확한지, 범용 부품으로 만든 핀 배열이 얼마나 빠르고 고르게 움직이는지는 확인되지 않았다.

본 연구의 목적은 일반 카메라 한 대와 범용 부품으로, 앞쪽 공간의 방향별 거리를 양 손바닥 아래 24개 핀의 높이로 전달하는 착용형 장치를 구현하고, 사용자 시험에 앞서 그 성능을 평가하는 것이다. 구체적으로 (1) 장치 카메라로 찍은 실내·실외 장면에서 거리 추정 오차와 그 보정 방법, (2) 소프트웨어 처리 시간과 핀이 반응하기까지의 시간, (3) 3D 프린팅 기구에서 24개 핀의 영점 높이 오차를 구한다. 반응 시간의 설계 요구는 물체가 나타난 뒤 0.5초 안에 핀이 움직이기 시작하고 1초 안에 목표 높이에 이르는 것으로 두었다. 보통 걷는 속도(약 1.2 m/s)에서 1초는 약 1.2 m에 해당한다. 사용자가 핀 높이를 구별하여 보행에 활용하는지는 이 결과를 바탕으로 한 후속 연구로 남긴다.

## Ⅱ. 연구 방법

### 2.1 연구 대상

본 연구의 평가 대상은 구현한 장치 1대이다. 사람을 대상으로 한 시험은 하지 않았으며, 핀 영점 보정(2.3 (4))에서 핀 윗면이 패드 표면과 같은 높이인지는 연구자가 눈과 손끝으로 판단하였다.

### 2.2 장치 구성

장치는 카메라, 연산부, 제어부, 촉각 패드로 이루어진다([그림 1]). 카메라(Logitech C920)는 패드 앞면에 수평으로 달았고(착용 시 렌즈 높이 땅에서 약 0.70 m), 1280 × 720, 초당 30프레임으로 영상을 받는다[16]. 걷는 동안 초점이 바뀌지 않도록 자동 초점을 끄고 초점을 무한대 쪽 끝으로 고정하였다. 연산부는 NVIDIA Jetson Orin Nano Super(메모리 8 GB, 25 W 모드)이며, 깊이 모델과 물체 검출 모델은 TensorRT FP16 엔진으로 실행한다.

![[그림 1] 장치 구성도](figures/final/fig_A1_system.png){width=7.2}

영상은 가운데 1280 × 698 영역을 924 × 504로 줄여 쓴다. 장면 판별은 Places365[17]로 학습한 ResNet18[18] 분류기가 초당 2회 하며, 실외로 분류된 범주 204개[19]의 확률을 더한 값을 시간 상수 1.0초로 평활하여, 0.65 이상이 1.5초 이어지면 실외, 0.35 이하가 1.5초 이어지면 실내로 판정한다. 깊이 추정에는 Depth Anything V2[15]의 ViT-S 모델을 쓴다. 실내로 판정되면 Hypersim[20]으로 학습된 미터 단위 모델의 출력에서 0.44 m를 빼서 쓴다. 이 값은 거리 정확도 실험(2.3 (2))의 실내 사진에서 이 모델이 실제보다 멀게 추정한 거리의 평균 차이이다. 실외로 판정되면 미터 단위로 미세조정하기 전의 상대 깊이 모델을 쓰고, 거리의 배율은 카메라 높이로 정한다(땅 기준 환산). 처음 설계에서는 Virtual KITTI 2[21]로 학습된 실외 미터 단위 모델을 썼으나, 같은 실험에서 이 모델이 보행 높이 영상의 거리를 수 배 멀게 추정하여(3.2) 바꾸었다.

땅 기준 환산은 상대 깊이 r이 깊이 Z에 반비례한다고 보고(r = A / Z), 카메라가 땅에서 높이 h에 수평으로 달려 있으면 화면 y번째 줄에 보이는 땅까지의 깊이가 Z(y) = f·h / (y − c<sub>y</sub>)라는 관계를 쓴다. 여기서 f는 화소 단위 초점거리, c<sub>y</sub>는 화면 가운데 줄이다. 프레임마다 땅까지 1.8~3.5 m에 해당하는 화면 아래쪽 줄들에서 줄별 r의 중앙값에 Z(y)를 곱하고, 그 중앙값을 A로 하여 모든 화소의 거리를 A / r로 구한다. h는 0.70 m, f는 908 화소(1280 × 720 기준)로 두었고, 걸을 때의 흔들림을 줄이도록 A의 로그 값을 시간 상수 1.0초로 평활한다. 이 방식은 땅이 평평하고 화면 아래쪽에 보인다고 가정한다.

깊이맵은 가로 6 × 세로 4칸으로 나누고, 칸마다 화소 거리의 하위 10번째 백분위를 대표 거리 d로 삼는다. 평균을 쓰면 칸의 일부만 차지하는 기둥이나 사람이 먼 배경에 묻히고, 최솟값을 쓰면 화소 하나의 잡음에 핀이 흔들리므로, 칸 넓이의 약 10 %를 차지하는 물체부터 반영되도록 정한 설계값이다(별도로 최적화하지는 않았다). d는 근접도 p = ln(d<sub>far</sub> / d) / ln(d<sub>far</sub> / 0.5 m)로 바꾸고(d는 0.5 m와 d<sub>far</sub> 사이로 제한), 7p를 반올림하여 단계 0~7을 얻는다. 가장 먼 표시 거리 d<sub>far</sub>는 실내 8 m, 실외 20 m로 두었다. 1.2 m/s로 걸을 때 각각 약 7초와 17초 앞에 해당하며, 실외는 공간이 넓어 먼 건물이나 트인 방향까지 거리감을 전하도록 실내보다 멀리 표시한다. 단계를 반올림하므로 핀이 올라오기 시작하는 거리는 실내 6.6 m, 실외 15.4 m이고, 한 단계마다 거리는 실내 약 1.49배, 실외 약 1.69배씩 커진다. 대표 거리는 가까워질 때 0.65, 멀어질 때 0.25의 계수로 지수 평활하고, 단계는 올라갈 때는 바로, 내려갈 때는 3프레임 연속으로 확인된 뒤 한 단계씩 바꾼다. 다가오는 물체는 빨리 알리고 멀어지는 변화는 확실할 때만 알리는 비대칭 설계이다.

위험 물체는 YOLO26n[22]으로 검출한다(입력 512 × 288, 신뢰도 0.40 이상). 자동차·자전거 등은 위험도 3, 사람·의자 등은 2, 신호등·화분 등은 1로 두고, 대표 거리가 4 m 이내인 칸의 핀을 위험도에 따라 1°, 2°, 3°씩 초당 10회 떨게 한다. 진동은 서보 위치 지령으로 만들기 때문에 핀 갱신 박자(0.2초)를 넷으로 나눈 구간 가운데 두 번째와 네 번째 구간에만 목표 위치를 비켜 놓으며, 손바닥의 진동 감각이 가장 예민한 주파수 대역(수백 Hz)보다 훨씬 낮다[23]. 진동은 목표 위치에 더해져 같은 속도 제한을 거치므로, 단계가 크게 바뀌는 동안에는 이동이 우선하고 진동은 핀이 목표 근처에 도착한 뒤 나타난다.

촉각 패드는 4행 × 6열, 24개 핀이며 핀 간격은 가로 30 mm, 세로 40 mm이다([그림 2]). 왼쪽 3열은 왼손, 오른쪽 3열은 오른손 손바닥이 맡고, 칸의 위치는 화면 위치와 그대로 대응한다. 핀 하나는 SG90 서보와 3D 프린팅한 12잇수 피니언(피치원 지름 16.00 mm)·랙으로 움직이며, PCA9685 PWM 드라이버[24] 두 개가 서보를 12개씩 맡는다. 구동 범위는 140 tick(핀 높이 0~9.0 mm, 보정 전 기준 232~372 tick)이며, 한 단계는 20 tick, 1.29 mm이다. 단계 0의 위치는 핀마다 따로 보정하였다(2.3 (4)). Jetson은 결과가 나올 때마다 31바이트 프레임(CRC-8 검사)을 USB로 Raspberry Pi Pico[25]에 보내고, Pico는 0.2초 박자마다 최신 값을 목표로 정해 5 ms마다 최대 4 tick씩 서보를 옮긴다. 유효한 프레임이 0.5초 동안 없으면 모든 핀을 10 ms에 1 tick씩 천천히 가장 낮은 위치로 내린다. Pico의 전원 자체가 끊기는 경우는 이 안전 기능의 범위 밖이며, 고찰에서 한계로 다룬다. 서보 전원은 3셀 리튬폴리머 배터리 두 개에서 강압 컨버터를 거쳐 드라이버마다 따로 공급하고, Jetson은 USB-C PD 보조배터리로 구동한다. 주요 설정값은 [표 1]과 같고, 구현 코드는 공개하였다[26].

[표 1] 장치 주요 설정값

| 항목 | 값 |
|---|---|
| 카메라 | Logitech C920, 1280 × 720, 30 fps, 초점 고정, 렌즈 높이 약 0.70 m |
| 깊이 입력 | 924 × 504 (가운데 1280 × 698에서 축소) |
| 장면 판별 | Places365 ResNet18, 초당 2회, 문턱 0.65 / 0.35, 유지 1.5 s |
| 깊이 추정 | Depth Anything V2 ViT-S. 실내: 미터 모델(Hypersim) − 0.44 m, 실외: 상대 깊이 + 땅 기준 환산(h 0.70 m, f 908 화소) |
| 칸 대표 거리 | 6 × 4칸, 하위 10번째 백분위 |
| 표시 거리 | 0.5 m ~ 실내 8 m / 실외 20 m, 로그 눈금 8단계 |
| 시간 필터 | 접근 0.65 / 후퇴 0.25 평활, 하강은 3프레임 확인 뒤 한 단계씩 |
| 위험 물체 | YOLO26n 512 × 288, 4 m 이내, 진동 1/2/3°, 초당 10회 |
| 핀 | 24개, 간격 30 × 40 mm, 0~9.0 mm, 단계당 1.29 mm, 핀별 영점 보정 |
| 갱신 | 박자 0.2 s, 5 ms마다 최대 4 tick, 통신 끊김 0.5 s 뒤 천천히 하강 |

![[그림 2] 촉각 패드와 핀 구동부의 3D 모델(설계 STL). (a) 베이스판과 서보 유닛 24개를 서보 쪽에서 본 모습이다. 손바닥은 반대쪽 평면에 닿고, 핀(랙)은 판의 구멍 24개를 지나 오르내린다. (b) 핀 하나의 구동부. SG90 서보가 12잇수 피니언(피치원 지름 16.00 mm)을 돌려 랙을 오르내리게 한다](figures/final/fig_hw_cad.png){width=7.2}

### 2.3 실험 절차

거리 정확도 실험의 결과에 따라 깊이 추정의 실내 보정값과 실외 방식을 바꾸었으며([표 1]은 바꾼 뒤의 값), 처리 시간은 바꾸기 전 설정(실외 Virtual KITTI 2 모델, 실내 보정 없음)으로 실내에서 측정하였다. 그 밖에 측정 기간에 바꾼 것은 핀 영점 보정(2.3 (4))뿐이다.

**(1) 소프트웨어 처리 시간.** 장치는 프레임마다 처리 단계별 소요 시간, 카메라 프레임이 Jetson에 들어온 뒤 처리가 시작되기까지의 대기 시간, 24칸의 거리·단계를 기록한다. 카메라부터 핀까지 모두 연결하고 확인 화면을 띄운 채 실내에서 실행한 기록 두 개(모두 7,894프레임)로 단계별 처리 시간과 대기 시간을 구하였다. 또 확인 화면을 띄우지 않고 Pico를 연결하지 않은 채 60초 동안 실행하여 처리율과 Jetson 모듈의 입력 전력(tegrastats의 VDD_IN, 1초 간격)을 측정하였다.

**(2) 거리 정확도.** 장치의 C920을 노트북에 연결하여 같은 초점 설정으로 1280 × 720 무손실 사진을 찍었다. 카메라는 손수레에 올려 렌즈가 땅에서 약 0.70 m에 오게 하고 눈대중으로 수평을 맞추었다. 가장 먼 거리의 사진에서 표적의 화면 위치로 역산한 기울기는 사진별 −1.1~+1.2°였다. 표적은 흰 상자의 앞면(가로 30 × 세로 27 cm)으로, 앞면 가운데가 렌즈 높이 근처에 오도록 렌즈 정면에 두었고, 거리는 렌즈에서 앞면까지 줄자로 재었다. 실외는 산책로와 주차장, 실내는 거실과 주방에서 찍었으며, 실외는 1, 2, 3, 4, 6, 8 m, 실내는 0.5, 1, 1.5, 2, 3, 4 m에서 거리마다 5장씩 모두 120장을 얻었다. 장소를 두 곳씩 둔 것은 한 장소에서 정한 보정값을 다른 장소에 적용해 보기 위해서이다. 사진마다 상자 앞면 영역을 손으로 표시하고, 장치와 같은 전처리를 거친 깊이 지도에서 그 영역을 사방 20 %씩 줄인 안쪽 화소의 중앙값을 그 사진의 추정 거리로 하였다. 깊이 지도는 처음 설계의 실내·실외 미터 단위 모델과 땅 기준 환산으로 모든 사진에 대해 구하였다.

**(3) 반응 시간.** 반응 시간은 Jetson이 카메라 프레임을 받아 Pico로 보내기까지의 프레임 대기와 처리 시간((1)에서 측정)과, 보낸 뒤 핀이 움직이기까지의 구동 지연으로 나누어 쟀다. 구동 지연을 재기 위해 깊이 추정을 거치지 않고 칸 9(위에서 둘째 줄, 왼쪽에서 넷째 칸)의 단계만 0과 7 사이에서 바꾸어 보내는 시험 프로그램을 만들었다. 프로그램은 평소 장치처럼 초당 15회 프레임을 계속 보내고, 단계를 바꾸는 프레임을 보낸 직후 모니터 창 전체를 흰색(0 → 7, 올림) 또는 검은색(7 → 0, 내림)으로 바꾸며, 보낸 시각과 화면 갱신 명령이 끝난 시각을 기록한다. 올림은 가까운 물체가 나타난 경우, 내림은 사라진 경우의 핀 움직임에 해당한다. 바꾸는 간격은 2.5~3.5초에서 무작위로 정하여 Pico의 0.2초 박자와 어긋나는 위치가 고르게 섞이게 하였다. 장치를 책상에 두고 스마트폰(Galaxy S10 5G)의 슬로 모션(초당 240프레임)으로 모니터와 칸 9의 핀을 한 화면에 담았다. 한 번의 녹화에서 올림과 내림을 10회씩 하였으며, 녹화 3번 가운데 스마트폰을 손에 들고 찍어 구도가 움직인 앞의 2번은 빼고, 스마트폰을 고정한 세 번째 녹화만 썼다. 영상에서 모니터 영역의 밝기가 흰색과 검은색의 중간값을 지나는 순간(앞뒤 프레임 사이 선형 보간)을 화면 전환 시각으로 하였다. 핀은 화면 전환 40프레임 전의 핀 윗부분을 본으로 삼아 프레임마다 정규화 상호상관으로 세로 위치를 찾았고, 옆의 고정 구조물도 같은 방식으로 추적하여 촬영 흔들림을 뺐다. 이동 전 위치와 이동 후 위치(차이 약 43.5화소, 9.0 mm) 사이의 진행률이 5 %를 넘는 순간을 움직임 시작, 95 %를 넘는 순간을 도착으로 하였다. 영상의 실제 촬영 속도는 화면 전환 시각을 프로그램 기록과 직선으로 맞추어 구하였다. 시작·도착 시간은 화면 전환 기준 값에 보낸 시각부터 화면 갱신 명령이 끝나기까지의 기록 시간을 더하여 보낸 시각 기준으로 나타냈다. 모니터가 실제로 화면을 바꾸기까지의 지연과 카메라 안에서 영상이 만들어져 Jetson에 도착하기까지의 지연은 재지 못하였으므로, 반응 시간은 실제보다 그만큼 짧게 나온다. 고정 구조물이 1화소 넘게 움직인 전환(촬영 흔들림)은 분석에서 뺐다. 측정은 핀 영점 보정 전 설정에서 하였다. 보정은 영점과 최대 위치를 같은 만큼 옮기므로 핀의 이동 거리와 시간에는 영향이 없다.

**(4) 핀 영점 오차.** 같은 지령에서 24개 핀의 높이가 조립 공차 때문에 얼마나 다른지를 소프트웨어 영점 보정의 보정량으로 구하였다. 보정 전에는 24핀 모두 단계 0이 372 tick, 단계 7이 232 tick이었다. 모든 핀을 단계 0에 두고, 전용 프로그램에서 핀을 하나씩 골라 핀 윗면이 패드 표면과 같아질 때까지 단계 0의 tick을 옮겼다(한 번에 1 또는 5 tick, 1 tick은 약 0.065 mm). 단계 7의 tick도 같은 수만큼 옮겨 스트로크(140 tick, 9.0 mm)는 유지하였다. 보정 범위는 보정 전 값에서 ±80 tick(약 5.2 mm)으로 제한하였다. 보정량(tick)에 tick당 높이를 곱한 값을 그 핀의 보정 전 영점 오차로 하였으며, 보정에서 핀을 내린 경우(보정 전에 패드 표면보다 높았던 경우)를 양수로 하였다. 보정 뒤 남은 오차는 따로 재지 않았다. 보정값은 장치의 보정 파일과 Pico 펌웨어의 기동 기본값에 함께 넣어, Jetson이 연결되기 전 기동 때에도 쓰이게 하였다.

### 2.4 분석 및 통계

처리 시간과 구동 지연은 평균, 표준편차, 중앙값, 범위, 95번째 백분위로 나타냈다. 두 측정은 따로 하였으므로, 설계 요구(시작 0.5초, 도착 1초 이내)는 구동 지연의 시행마다 프레임 대기와 처리 시간을 합한 값의 95번째 백분위를 더하여 판단하고, 만족한 시행의 비율을 구하였다. 거리 정확도는 사진마다 상대 오차 (추정 거리 − 실제 거리) / 실제 거리 × 100 %를 구하고, 그 절댓값의 평균(MAPE)을 장소·방법·거리별로 정리하였다. 처음 설계의 미터 단위 모델에는 곱하기(원점을 지나는 최소제곱 배율), 더하기, 1차식, 거듭제곱 보정을 적용해 보았고, 보정값은 한 장소의 사진으로 정해 다른 장소의 사진에 적용(장소 교차)하여 평가하였다. 땅 기준 환산은 표적 거리를 쓰지 않으므로 모든 사진에 그대로 적용하였다. 표시 단계는 [표 1]의 매핑(시간 필터 제외)으로 실제 거리와 추정 거리를 각각 단계로 바꾸어 일치율과 ±1단계 이내 비율을 구하였다(실내 사진 d<sub>far</sub> 8 m, 실외 사진 20 m). 같은 거리에서 연달아 찍은 5장은 서로 독립이 아니므로, 두 방법의 비교는 장소 × 거리 묶음별 평균 오차를 단위로 윌콕슨 부호순위 검정과 묶음 부트스트랩(10,000회) 95 % 신뢰구간으로 하였다. 분석 값은 장치 코드(TensorRT FP16)로 다시 계산하여 확인하였다(사진별 차이 최대 1.3 %). 핀 영점 오차는 24핀의 평균, 표준편차, 절댓값의 평균과 중앙값, 범위로 나타내고, 한 단계 높이(20 tick, 1.29 mm)와 비교하였다. 분석에는 Python과 SciPy를 사용하였고 유의수준은 0.05로 하였다.

## Ⅲ. 결  과

### 3.1 소프트웨어 처리 시간

실내 실행 기록 7,894프레임에서 한 프레임의 처리 시간(처리 시작부터 Pico로 보내기까지)은 평균 68.8 ms, 중앙값 65.5 ms, 95번째 백분위 82.4 ms였다([표 2]). 깊이 추정이 평균 48.5 ms로 가장 길었고, 위험 물체 검출이 14.7 ms였다. 장면 판별은 전체 프레임의 21.3 %(1,680프레임)에서 실행되었고, 그 프레임에서 평균 20.4 ms가 더해졌다. 필터·매핑과 USB 전송은 합쳐서 1.1 ms였다. 카메라 프레임이 Jetson에 들어온 뒤 처리가 시작되기까지의 대기는 평균 34.8 ms였으며, 대기와 처리를 합한 시간은 프레임별로 평균 103.6 ms, 95번째 백분위 137.4 ms, 최대 166.7 ms였다.

확인 화면 없이 60초 동안 실행했을 때는 918프레임을 처리하여 초당 15.3프레임이었고, 처리 시간은 중앙값 64.1 ms, 95번째 백분위 85.9 ms였다. 이때 Jetson 모듈의 입력 전력은 중앙값 14.4 W, 최대 15.1 W였다. 이 측정들은 깊이 추정을 바꾸기 전 설정에서 한 것이며(2.3), 바꾼 뒤 깊이 추정만 따로 잰 시간(30회 예열 뒤 최솟값)은 실내 39.6 ms, 실외 40.6 ms로 바꾸기 전 실내 39.5 ms와 1.1 ms 이내였다.

[표 2] 소프트웨어 단계별 처리 시간 (실내 7,894프레임, ms)

| 단계 | 평균 | 표준 편차 | 중앙값 | 95 백분위 | 최대 |
|---|---|---|---|---|---|
| 대기 (수신 → 처리 시작) | 34.8 | 15.5 | 32.5 | 70.1 | 87.3 |
| 깊이 추정 (실내 모델) | 48.5 | 3.4 | 48.2 | 55.2 | 78.5 |
| 위험 물체 검출 | 14.7 | 1.4 | 15.1 | 16.3 | 21.9 |
| 장면 판별 (1,680프레임) | 20.4 | 2.1 | 21.0 | 22.4 | 50.1 |
| 필터·매핑 | 0.5 | 0.1 | 0.5 | 0.7 | 3.1 |
| USB 전송 | 0.6 | 0.4 | 0.6 | 0.7 | 9.5 |
| 처리 (처리 시작 → 보냄) | 68.8 | 7.3 | 65.5 | 82.4 | 114.4 |
| 대기 + 처리 | 103.6 | 16.6 | 101.5 | 137.4 | 166.7 |

주: 처리는 단계별 시간과 그 밖의 처리를 모두 포함한 프레임 전체 시간이며, 확인 화면을 그리는 시간은 들어 있지 않다.

### 3.2 거리 정확도

방법별 오차와 표시 단계 일치율은 [표 3], 거리별 추정 거리는 [그림 3]과 같다.

실내 사진에서 실내 모델은 모든 거리에서 실제보다 멀게 추정하였다(장소 합침 평균 0.5 m → 0.94 m, 1 m → 1.37 m, 4 m → 4.43 m). 실제와의 차이는 거리에 따라 크게 변하지 않았으며, 평균은 거실 0.47 m, 주방 0.41 m, 전체 0.44 m였다. 다른 장소의 평균 차이를 빼서 보정하면 MAPE는 34.3 %에서 9.5 %가 되었고, 곱하기 보정은 18.0 %, 1차식과 거듭제곱 보정은 각각 9.4 %, 9.6 %였다.

실외 사진에서 실외 모델은 1 m를 평균 8.82 m, 8 m를 27.28 m로 추정하였다(장소 합침). 화면 아래쪽 땅(기하 거리 1.82~3.5 m)에서 이 모델의 깊이는 기하 거리의 3.11~3.69배(장소별 중앙값)였다. 곱하기 배율은 산책로 0.257, 주차장 0.157이었고, 장소 교차 보정 후 MAPE는 곱하기 63.2 %, 다른 보정 70.2~172.0 %였다. 같은 사진에서 실내 모델 − 0.44 m의 MAPE는 38.0 %(산책로 6.7 %, 주차장 69.3 %), 땅 기준 환산은 21.1 %(산책로 10.9 %, 주차장 31.2 %)였다. 땅 기준 환산의 오차는 실내 모델 − 0.44 m보다 묶음 평균 16.9 %p 작았고(95 % 신뢰구간 −32.1 ~ −2.9 %p), 12묶음 중 7개에서 작았다(윌콕슨 p = 0.092). 땅 기준 환산을 실내 사진에 적용하면 MAPE는 54.8 %였다.

가정한 카메라 기울기가 실제와 1° 다르면 땅 기준 환산의 실외 MAPE는 16.8~26.3 %, 3° 다르면 12.6~41.3 %였고, 가정한 높이가 5 cm 다르면 16.1~27.3 %, 10 cm 다르면 13.5~34.9 %였다.

[표 3] 거리 정확도 — 방법별 MAPE(%)와 표시 단계 일치율(%)

| 방법 | 장소 1 | 장소 2 | 전체 | 단계 일치 | ±1단계 |
|---|---|---|---|---|---|
| § 실내 사진 (d<sub>far</sub> 8 m) | | | | | |
| 실내 모델 | 34.6 | 34.0 | 34.3 | 60 | 92 |
| 실내 모델 × 배율 (장소 교차) | 17.8 | 18.3 | 18.0 | 70 | 98 |
| 실내 모델 − 차이 (장소 교차) | 10.5 | 8.5 | 9.5 | 75 | 100 |
| § 실외 사진 (d<sub>far</sub> 20 m) | | | | | |
| 실외 모델 | 447.2 | 589.8 | 518.5 | 0 | 0 |
| 실외 모델 × 배율 (장소 교차) | 48.1 | 78.2 | 63.2 | 25 | 80 |
| 실내 모델 − 0.44 m | 6.7 | 69.3 | 38.0 | 55 | 92 |
| 땅 기준 환산 | 10.9 | 31.2 | 21.1 | 60 | 100 |

주: 장소 1·2는 실내가 거실·주방, 실외가 산책로·주차장이며 장소마다 30장이다.

![[그림 3] 줄자 거리와 추정 거리(로그 눈금). (a) 실내 사진: 실내 모델 보정 전과, 다른 장소의 평균 차이로 보정한 값. (b) 실외 사진: 실외 모델 보정 전과 땅 기준 환산. 점은 같은 거리 5장의 평균, 막대는 표준편차, 점선은 추정 = 실제](figures/final/fig_A2_distance.png){width=7.2}

### 3.3 반응 시간

세 번째 녹화의 전환 20회 가운데 촬영이 흔들린 3회(올림 2회, 내림 1회)를 빼고 17회(올림 8회, 내림 9회)를 분석하였다. 영상의 실제 촬영 속도는 초당 235.05프레임이었고, 화면 전환 시각을 프로그램 기록에 맞춘 잔차는 표준편차 17.7 ms(최대 31.7 ms)였다. 보낸 시각부터 화면 갱신 명령이 끝나기까지는 평균 27.2 ms(26.4~28.7 ms)였다.

Jetson이 보낸 뒤 핀이 움직이기 시작하기까지는 평균 116.3 ms(41.6~215.7 ms), 도착하기까지는 평균 280.1 ms(190.1~379.2 ms)였다([표 4], [그림 4]). 움직이기 시작해서 도착하기까지는 평균 163.8 ms(표준편차 6.8 ms, 148.5~175.2 ms)였다. 도착 시간의 평균은 올림 296.6 ms, 내림 265.4 ms였다.

3.1의 대기와 처리를 합한 시간의 평균(103.6 ms)을 더하면 반응 시간은 시작 평균 219.9 ms, 도착 평균 383.7 ms이다. 그 95번째 백분위(137.4 ms)를 더하면 시작은 최대 353.1 ms, 도착은 최대 516.6 ms로 17회 모두 설계 요구(시작 0.5초, 도착 1초 이내)를 만족하였고, 최댓값(166.7 ms)을 더해도 시작은 최대 382.4 ms, 도착은 최대 545.9 ms였다.

[표 4] 구동 지연 — Jetson이 보낸 뒤 핀이 움직이기까지 (ms)

| 구간 | 횟수 | 평균 | 표준 편차 | 범위 | 95 백분위 |
|---|---|---|---|---|---|
| § 올림 (0 → 7단계) | | | | | |
| 보냄 → 시작 | 8 | 130.0 | 67.6 | 50.7~215.7 | 211.4 |
| 보냄 → 도착 | 8 | 296.6 | 66.3 | 220.1~379.2 | 377.6 |
| 시작 → 도착 | 8 | 166.6 | 6.9 | 155.1~175.2 | 174.9 |
| § 내림 (7 → 0단계) | | | | | |
| 보냄 → 시작 | 9 | 104.1 | 39.1 | 41.6~160.8 | 148.9 |
| 보냄 → 도착 | 9 | 265.4 | 43.3 | 190.1~323.8 | 313.8 |
| 시작 → 도착 | 9 | 161.4 | 5.9 | 148.5~168.1 | 167.5 |
| § 전체 | | | | | |
| 보냄 → 시작 | 17 | 116.3 | 54.2 | 41.6~215.7 | 205.9 |
| 보냄 → 도착 | 17 | 280.1 | 55.8 | 190.1~379.2 | 375.6 |
| 시작 → 도착 | 17 | 163.8 | 6.8 | 148.5~175.2 | 174.6 |

주: 시작 = 이동 거리(9.0 mm)의 5 %, 도착 = 95 %. 모니터 표시 지연은 빠져 있다(2.3 (3)).

![[그림 4] 핀 이동 진행률. (a) 올림, (b) 내림. 선은 시행 하나, 동그라미는 움직임 시작, 네모는 도착, 점선은 Jetson이 보낸 시각](figures/final/fig_A3_latency.png){width=6.6}

### 3.4 핀 영점 오차

보정 전 24개 핀의 영점 오차는 평균 0.00 mm, 표준편차 2.20 mm, 절댓값의 평균 1.61 mm(중앙값 1.29 mm), 범위 −3.55 ~ +5.17 mm였다([표 5]). 보정이 필요 없던 핀은 5개였고, 8개는 패드 표면보다 높았으며 11개는 낮았다. 오차가 한 단계(20 tick, 1.29 mm) 이하인 핀은 13개(보정이 필요 없던 5개 포함), 두 단계를 넘는 핀은 7개였고, 가장 큰 오차는 네 단계에 해당하였다. 칸 5는 보정 범위의 끝(80 tick)까지 옮겼으므로 실제 오차는 5.17 mm보다 클 수 있다.

[표 5] 핀별 보정 전 영점 오차 (mm)

| 행 | 1열 | 2열 | 3열 | 4열 | 5열 | 6열 |
|---|---|---|---|---|---|---|
| 1 | +3.23 | +0.65 | 0.00 | −1.94 | +1.61 | +5.17 |
| 2 | 0.00 | −0.32 | −0.97 | −3.55 | 0.00 | +1.29 |
| 3 | −3.23 | −0.65 | −0.97 | −2.58 | −3.23 | 0.00 |
| 4 | 0.00 | +1.29 | −0.32 | −1.61 | +2.91 | +3.23 |

주: 칸 배치는 화면과 같다(1~3열 왼손, 4~6열 오른손). + = 보정 전 패드 표면보다 높음. 1행 6열(칸 5)은 보정 범위의 끝까지 옮긴 값이다.

## Ⅳ. 고  찰

실내 모델은 0.5~4 m에서 거리와 거의 상관없이 약 0.44 m 멀게 추정하였다. 오차가 거리에 비례하였다면 곱하기 보정이 맞았겠지만, 실제로는 더하기 보정(MAPE 9.5 %)이 곱하기 보정(18.0 %)보다 정확하였고 모수가 둘인 1차식(9.4 %)과도 차이가 거의 없어, 모수 하나인 더하기 보정을 장치에 넣었다. 이 차이가 생긴 원인은 확인하지 못하였다. 또 보정값은 세워 둔 상자의 앞면으로 정한 것이어서, 화면 아래쪽의 바닥처럼 비스듬히 보이는 면에도 같은 차이가 있는지는 확인하지 않았다. 바닥에서 차이가 이보다 작다면 맨 아래 줄의 바닥이 실제보다 가깝게 표시되어 핀이 한 단계 가까이 높게 나올 수 있다. 0.5 m에서는 보정 뒤에도 사진 사이의 흩어짐이 컸다.

실외 미터 단위 모델의 큰 과대 추정은 학습 영상과 장치 카메라의 차이로 대부분 설명된다. Virtual KITTI 2의 카메라 높이를 KITTI와 같은 약 1.65 m로 보면 장치 카메라(0.70 m)보다 두 배 이상 높다. 같은 화면 위치에 보이는 땅은 카메라가 낮을수록 가까우므로, 높은 카메라로 학습한 모델은 낮은 카메라의 장면을 멀게 보게 된다. 카메라 높이 비와 화각 차이로 계산한 배율은 약 3.5배였고, 실제로 화면 아래쪽 땅에서 이 모델의 깊이는 기하 거리의 3.11~3.69배였다. 단안 영상에서 추정한 절대 거리가 카메라 조건에 묶여 있다는 점은 선행연구에서도 지적되었다[27]. 땅 기준 환산은 반대로 알려진 카메라 높이로 배율을 정하는 방식으로, 차량의 단안 영상 주행 거리 추정에서 쓰인 땅 평면 기반 배율 추정[28, 29]과 같은 생각을 착용형 장치의 매 프레임에 적용한 것이다. 이 방식은 표적 거리를 쓰지 않고도 실외 MAPE를 21.1 %로 낮추었으나, 주차장(31.2 %)에서 산책로(10.9 %)보다 오차가 컸다. 기울기를 1° 잘못 가정하면 MAPE가 약 5 %p 달라졌으므로, 땅의 경사와 카메라 기울기가 남은 오차의 주된 원인일 가능성이 있다. 걷는 동안에는 몸통이 앞뒤로 기울어지므로, 실제 사용에서는 관성 센서로 기울기를 재어 보정할 필요가 있다. 실내에서는 가까운 물체가 화면 아래의 바닥을 가려 이 방식을 쓸 수 없었다(MAPE 54.8 %).

장면에 따라 깊이 추정 방식과 가장 먼 표시 거리가 바뀌므로, 같은 거리의 물체도 실내와 실외에서 다른 높이로 표시된다. 예를 들어 4 m의 물체는 실내에서 단계 2, 실외에서 단계 3이다. 실외를 실내보다 멀리 표시하는 것은 넓은 공간의 거리감을 전하려는 선택이지만, 사용자는 두 가지 눈금을 익혀야 하고 장면 판정이 바뀌는 순간 핀 높이가 함께 바뀐다. 이번 측정은 장면별 정확도만 보았으므로, 눈금을 하나로 통일하는 것과 비교하여 어느 쪽이 사용자에게 나은지는 사용자 시험으로 정해야 한다.

반응 시간에서 깊이 추정이 차지하는 시간은 평균 48.5 ms로 작았다. 핀이 움직이기 시작하기까지의 시간은 41.6~215.7 ms로 Pico의 0.2초 박자 폭만큼 퍼져 있었고, 평균(116.3 ms)도 박자 대기의 기대값(100 ms)에 가까웠다. 움직이기 시작해서 도착하기까지의 163.8 ms는 펌웨어 속도 제한(5 ms마다 4 tick)으로 계산한 5~95 % 이동 시간 157.5 ms와 비슷하였다. 즉 반응 시간은 계산보다 구동부의 박자와 속도 제한으로 정해졌다. 박자를 0.1초로 줄이면 대기는 평균 50 ms로 줄지만, 현재 구동 범위는 한 박자 안에 끝에서 끝까지 움직이도록 정한 것이어서 큰 변화가 두 박자에 나뉘게 된다. 측정에서 빠진 카메라 내부 지연과 모니터 표시 지연은 반응 시간을 늘리는 방향이므로, 도착 시간 최댓값(545.9 ms)과 요구(1초) 사이의 여유는 그만큼 줄어든다. 측정은 칸 하나의 단계 0과 7 사이 이동만 다루었고, 24개 핀이 함께 움직일 때 전원 전압이 떨어지는 경우는 포함하지 않았다.

보정 전 핀 영점 오차의 표준편차(2.20 mm)는 한 단계 높이(1.29 mm)보다 컸다. 보정하지 않으면 같은 단계를 내더라도 핀마다 높이가 한 단계 넘게 달라 거리 차이와 구별되지 않는다. 3 mm가 넘는 오차는 6개였는데, 이는 피니언 이 하나에 해당하는 약 4.2 mm와 비슷한 크기여서 조립할 때 랙과 피니언이 한 이 어긋나게 맞물린 경우로 설명될 수 있다(확인하지는 않았다). 소프트웨어 보정은 기구를 다시 조립하지 않고 이 차이를 줄일 수 있어 3D 프린팅으로 만든 저가 기구에 알맞다. 다만 보정은 눈과 손끝으로 맞춘 것이어서 보정 뒤 남은 오차는 재지 않았고, 칸 5는 보정 범위의 끝에 걸려 다시 조립해야 할 수 있다.

본 연구의 한계는 다음과 같다. 첫째, 사용자 시험을 하지 않았다. 손바닥이 1.29 mm의 단계 차이를 구별하는지, 장치를 쓰며 걸을 때 흰지팡이만 쓸 때보다 충돌이 줄어드는지는 이번 결과로 말할 수 없다. 둘째, 거리 정확도는 실내·실외 두 곳씩의 정지 사진에서 잰 것으로, 걸을 때의 흔들림과 계단·유리처럼 깊이 추정이 어려운 대상은 포함하지 않았다. 또 렌즈 높이 0.70 m에서 세로 반화각은 약 21°이므로, 앞쪽 1.8 m 안의 바닥과 머리 높이(1.5~1.7 m)에서 약 2.1~2.6 m보다 가까운 물체는 화면 밖에 있다. 셋째, 처리 시간은 깊이 추정 방식을 바꾸기 전 설정에서 재었다(바꾼 뒤 추론 시간 차이 1.1 ms 이내). 넷째, 위험 물체 진동(1~3°)이 손바닥에 느껴지는지와 서보 소리의 크기를 재지 않았다. 다섯째, 통신이 끊기면 핀이 가장 낮은 위치로 내려가는데, 이 상태는 앞이 비어 있다는 표시와 구별되지 않는다. 또 Pico의 전원이 끊기면 서보가 힘을 잃어 소프트웨어로 핀을 내릴 수 없다. 고장을 알리는 별도의 신호가 필요하다.

## Ⅴ. 결  론

본 연구는 일반 카메라 한 대와 범용 부품으로 앞쪽 공간의 방향별 거리를 양 손바닥 아래 24개 핀의 높이로 전달하는 착용형 보행 보조 장치를 구현하고, 처리 시간, 거리 정확도, 반응 시간, 핀 영점 오차를 측정하였다. 장치는 한 프레임을 평균 68.8 ms에 처리하였고, 처리 시간을 더한 반응 시간은 17회 모두 설계 요구(시작 0.5초, 도착 1초 이내)를 만족하였다. 반응 시간의 대부분은 깊이 추정이 아니라 핀 갱신 박자와 서보 이동이 차지하였다. 단안 미터 깊이 모델은 장치 카메라에서 그대로 쓸 수 없었으며, 실내에서는 0.44 m를 빼는 보정으로 MAPE 9.5 %, 실외에서는 카메라 높이를 이용한 땅 기준 환산으로 MAPE 21.1 %를 얻어, 모든 사진에서 표시 단계가 실제와 1단계 이내였다. 3D 프린팅 기구의 영점 오차(표준편차 2.20 mm)는 한 단계보다 커서 핀별 소프트웨어 보정이 필요하였다. 앞으로 손바닥의 핀 높이 구별 시험과 흰지팡이와 함께 쓰는 보행 시험으로 사용자 측면의 효과를 확인하고, 걸을 때의 카메라 기울기 보정과 고장 알림 신호를 더할 계획이다. 장치의 구현 코드는 공개하였다[26].

## 참고문헌

[1] World Health Organization, “Blindness and vision impairment,” Fact sheet, Feb. 2026. [Online]. Available: https://www.who.int/news-room/fact-sheets/detail/blindness-and-visual-impairment

[2] GBD 2019 Blindness and Vision Impairment Collaborators and Vision Loss Expert Group of the Global Burden of Disease Study, “Trends in prevalence of blindness and distance and near vision impairment over 30 years: an analysis for the Global Burden of Disease Study,” *The Lancet Global Health*, vol. 9, no. 2, pp. e130–e143, 2021. https://doi.org/10.1016/S2214-109X(20)30425-3

[3] 보건복지부, “2023년 등록장애인 현황,” 2024년 4월 발표. 보도: J. Lee, “5.1% of Korean population registered as disabled in 2023: report,” *The Korea Herald*, Apr. 18, 2024.

[4] R. Manduchi and S. Kurniawan, “Mobility-related accidents experienced by people with visual impairment,” *Insight: Research and Practice in Visual Impairment and Blindness*, vol. 4, no. 2, pp. 44–54, 2011.

[5] P. Bach-y-Rita, C. C. Collins, F. A. Saunders, B. White, and L. Scadden, “Vision substitution by tactile image projection,” *Nature*, vol. 221, no. 5184, pp. 963–964, 1969. https://doi.org/10.1038/221963a0

[6] N. Sadato, A. Pascual-Leone, J. Grafman, V. Ibañez, M.-P. Deiber, G. Dold, and M. Hallett, “Activation of the primary visual cortex by Braille reading in blind subjects,” *Nature*, vol. 380, no. 6574, pp. 526–528, 1996. https://doi.org/10.1038/380526a0

[7] M. Ptito, S. M. Moesgaard, A. Gjedde, and R. Kupers, “Cross-modal plasticity revealed by electrotactile stimulation of the tongue in the congenitally blind,” *Brain*, vol. 128, no. 3, pp. 606–614, 2005. https://doi.org/10.1093/brain/awh380

[8] U.S. Food and Drug Administration, “De Novo classification request for BrainPort V100 (DEN130039),” Jun. 2015.

[9] P. Grant, L. Spencer, A. Arnoldussen, R. Hogle, A. Nau, J. Szlyk, J. Nussdorf, D. C. Fletcher, K. Gordon, and W. Seiple, “The functional performance of the BrainPort V100 device in persons who are profoundly blind,” *Journal of Visual Impairment & Blindness*, vol. 110, no. 2, pp. 77–88, 2016. https://doi.org/10.1177/0145482X1611000202

[10] P. B. L. Meijer, “An experimental system for auditory image representations,” *IEEE Transactions on Biomedical Engineering*, vol. 39, no. 2, pp. 112–121, 1992. https://doi.org/10.1109/10.121642

[11] D. Dakopoulos and N. G. Bourbakis, “Wearable obstacle avoidance electronic travel aids for blind: a survey,” *IEEE Transactions on Systems, Man, and Cybernetics, Part C*, vol. 40, no. 1, pp. 25–35, 2010. https://doi.org/10.1109/TSMCC.2009.2021255

[12] W. Elmannai and K. Elleithy, “Sensor-based assistive devices for visually-impaired people: current status, challenges, and future directions,” *Sensors*, vol. 17, no. 3, art. 565, 2017. https://doi.org/10.3390/s17030565

[13] R. K. Katzschmann, B. Araki, and D. Rus, “Safe local navigation for visually impaired users with a time-of-flight and haptic feedback device,” *IEEE Transactions on Neural Systems and Rehabilitation Engineering*, vol. 26, no. 3, pp. 583–593, 2018. https://doi.org/10.1109/TNSRE.2018.2800665

[14] F. Vidal-Verdú and M. Hafez, “Graphical tactile displays for visually-impaired people,” *IEEE Transactions on Neural Systems and Rehabilitation Engineering*, vol. 15, no. 1, pp. 119–130, 2007. https://doi.org/10.1109/TNSRE.2007.891375

[15] L. Yang, B. Kang, Z. Huang, Z. Zhao, X. Xu, J. Feng, and H. Zhao, “Depth Anything V2,” in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 37, pp. 21875–21911, 2024. https://doi.org/10.52202/079017-0688

[16] Logitech, “HD Pro Webcam C920 technical specifications.” [Online]. Available: https://support.logi.com

[17] B. Zhou, A. Lapedriza, A. Khosla, A. Oliva, and A. Torralba, “Places: A 10 million image database for scene recognition,” *IEEE Transactions on Pattern Analysis and Machine Intelligence*, vol. 40, no. 6, pp. 1452–1464, 2018. https://doi.org/10.1109/TPAMI.2017.2723009

[18] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image recognition,” in *Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2016, pp. 770–778. https://doi.org/10.1109/CVPR.2016.90

[19] CSAILVision, “Places365: The 365 scene categories and pretrained CNNs.” [Online]. Available: https://github.com/CSAILVision/places365

[20] M. Roberts, J. Ramapuram, A. Ranjan, A. Kumar, M. A. Bautista, N. Paczan, R. Webb, and J. M. Susskind, “Hypersim: A photorealistic synthetic dataset for holistic indoor scene understanding,” in *Proc. IEEE/CVF International Conference on Computer Vision (ICCV)*, 2021, pp. 10892–10902. https://doi.org/10.1109/ICCV48922.2021.01073

[21] Y. Cabon, N. Murray, and M. Humenberger, “Virtual KITTI 2,” arXiv:2001.10773, 2020. https://doi.org/10.48550/arXiv.2001.10773

[22] Ultralytics, “Ultralytics YOLO26.” [Online]. Available: https://docs.ultralytics.com/models/yolo26/

[23] K. O. Johnson, “The roles and functions of cutaneous mechanoreceptors,” *Current Opinion in Neurobiology*, vol. 11, no. 4, pp. 455–461, 2001. https://doi.org/10.1016/S0959-4388(00)00234-8

[24] NXP Semiconductors, “PCA9685: 16-channel, 12-bit PWM Fm+ I²C-bus LED controller,” Product data sheet, Rev. 4, 2015.

[25] Raspberry Pi Ltd, “RP2040 Datasheet: A microcontroller by Raspberry Pi.” [Online]. Available: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf

[26] 오형준, “tactile-vision: 단안 깊이 추정 기반 촉각 보행 보조 장치,” GitHub 저장소, 커밋 〔ground-scale 가지 공개 후 기입〕, 2026. [Online]. Available: https://github.com/MuakTiger/tactile-vision

[27] W. Yin, C. Zhang, H. Chen, Z. Cai, G. Yu, K. Wang, X. Chen, and C. Shen, “Metric3D: Towards zero-shot metric 3D prediction from a single image,” in *Proc. IEEE/CVF International Conference on Computer Vision (ICCV)*, 2023, pp. 9009–9019. https://doi.org/10.1109/ICCV51070.2023.00830

[28] S. Song and M. Chandraker, “Robust scale estimation in real-time monocular SFM for autonomous driving,” in *Proc. IEEE Conference on Computer Vision and Pattern Recognition (CVPR)*, 2014, pp. 1566–1573. https://doi.org/10.1109/CVPR.2014.203

[29] D. Zhou, Y. Dai, and H. Li, “Ground-plane-based absolute scale estimation for monocular visual odometry,” *IEEE Transactions on Intelligent Transportation Systems*, vol. 21, no. 2, pp. 791–802, 2020. https://doi.org/10.1109/TITS.2019.2900330
