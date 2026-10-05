# HANDOFF — 다른 AI 도구(Claude Code, Codex 등)에서 이어가기

작성: 2026-10-06. 이 문서와 `FACTS.md`만 읽으면 지금까지의 작업 전체를 이어받을 수 있게 정리했다.
수치·사실의 근거는 `FACTS.md`가 원장이다(이 문서는 길잡이). 토큰·비밀번호 값은 어디에도 적지 않았다.

---

## 0. 새 도구에 처음 붙여 넣을 프롬프트

**A. 이 젯슨에서 직접 실행하는 경우 (권장 — 파일·Pico·카메라를 직접 다룰 수 있음)**

```text
이 컴퓨터(NVIDIA Jetson Orin Nano, Ubuntu 24.04, 사용자 june)에서 내 졸업 프로젝트를 이어서 도와줘.
이전 AI 도구에서 하던 작업이고, 인계 문서가 있어.

1) 먼저 아래 파일을 순서대로 읽어:
   - ~/github/tactile-vision-thesis/HANDOFF.md   (인계 문서, 가장 먼저)
   - ~/github/tactile-vision-thesis/FACTS.md     (확정 사실 원장)
   - ~/tactile-vision/README.md                  (장치 코드 설명)
2) 읽은 뒤 현재 상태를 7줄 이내로 요약하고, HANDOFF.md 8절의 남은 일 중 무엇부터 할지 나한테 물어봐. 내가 답하기 전에는 파일을 바꾸거나 명령을 실행하지 마.
3) 규칙은 HANDOFF.md 6절을 따라. 특히: 한국어로 짧고 쉽게 답하기, 토큰 값 출력·저장 금지,
   논문 초안 v1·v2 수정 금지, 핀(서보)을 움직이는 명령은 실행 전에 말해 주기, 공개 저장소 push는 물어보고 하기.
```

**B. 웹 버전이라 이 컴퓨터에 접근할 수 없는 경우**

```text
GitHub 비공개 저장소 MuakTiger/tactile-vision-thesis 의 HANDOFF.md 와 FACTS.md, 그리고 공개 저장소
MuakTiger/tactile-vision 의 README.md 를 읽고 내 졸업 프로젝트를 이어서 도와줘.
읽은 뒤 현재 상태를 7줄 이내로 요약하고 무엇부터 할지 물어봐. 규칙은 HANDOFF.md 6절을 따라.
(너는 젯슨 로컬 파일과 하드웨어에 접근할 수 없으니, 명령이 필요하면 내가 젯슨 터미널에서 실행할 수 있게 알려 줘.)
```

웹 버전은 비공개 저장소를 읽을 수 있도록 GitHub 연결 권한을 따로 줘야 하고, 젯슨에만 있는 파일(아래 2절의 "로컬만")은 볼 수 없다.

---

## 1. 프로젝트 요약

- **무엇**: 시각장애인용 착용형 시각→촉각 감각 대체 장치 (을지대학교 의료공학과 졸업 프로젝트, 2021148015 오형준, 지도교수 하지현).
- **처리 흐름**: Logitech C920 카메라 → Jetson Orin Nano Super(25 W)에서 Places365 실내/실외 판별(초당 2회) → Depth Anything V2 metric 깊이(실내 Hypersim / 실외 VKITTI, TensorRT FP16, 924×504) → 24칸(6열×4행) 하위 10% 거리 → 로그 매핑 0.5 m~d_far(실내 4 m / 실외 8 m), 8단계, 비대칭 필터 → YOLO26n 위험 물체(위험도 1/2/3 → 핀 진동 1°/2°/3°, 초당 10회, 4 m 이내) → USB 31바이트 프레임(CRC-8) → Raspberry Pi Pico(펌웨어 v3, 0.2 s 박자로 최신 값 적용) → I²C PCA9685 ×2 → SG90 ×24 → 3D 프린팅 랙·피니언 핀(양손 손바닥, 9.0 mm 스트로크).
- **현재 단계**: 장치 실전 구동 확인 완료(카메라→Pico→24핀). 졸업논문 v3 초안 완성 — **단 실험 1~3 수치는 예시값**(실험 미수행). 다음은 실제 실험과 수치 교체.

---

## 2. 위치

| 무엇 | 위치 | 비고 |
|---|---|---|
| 장치 코드 (작업본) | 젯슨 `~/tactile-vision/` | git, 원격 = 공개 저장소 |
| 공개 코드 저장소 | https://github.com/MuakTiger/tactile-vision | MIT, main `632b1a1`. 모델 가중치·엔진 제외 |
| 논문·원장 저장소 | https://github.com/MuakTiger/tactile-vision-thesis (비공개) / 젯슨 `~/github/tactile-vision-thesis/` | `FACTS.md`, `thesis/`, 이 문서 |
| 논문 v3 | `thesis/졸업논문_v3.md` (+ `.docx`, `.pdf` 39쪽), 그림 `thesis/figures/v3/`, 분석 `thesis/analysis/` | 바탕화면 사본 `~/Desktop/촉각비전_졸업논문_v3/` |
| 이전 논문 초안 | `thesis/졸업논문_초안.md`(v1), `thesis/졸업논문_초안_v2.md`(v2), `졸업논문.txt` | **수정 금지** |
| 코드 사본 | `~/Desktop/v3/` | `rsync -a --delete --exclude '__pycache__' ~/tactile-vision/ ~/Desktop/v3/` 로 맞춤 |
| 모델 파일 (로컬만) | `~/tactile-vision/models/` (ONNX·TRT 엔진), `~/tactile-vision/checkpoints/` (.pth, yolo26n.pt, places365/) | 약 840 MB, 저장소에 없음. 받는 곳은 README "모델 파일" |
| 원본 보행 영상 (로컬만) | `~/Downloads/drive-download-20261005T105756Z-1-001/` (아이폰 MOV 14개, 1.5 GB) | 사람 얼굴 포함 — 공개 금지 |
| 바로 보는 MP4 (로컬만) | `~/Desktop/촉각비전_원본영상_mp4/` (H.264, HLG→SDR, 1.9 GB) | |
| 처리 샘플 영상 (로컬만) | `~/Desktop/촉각비전_샘플영상/` (14개 4칸 화면, 546 MB), CSV·로그는 `_데이터/` | |
| 정리 메모 | `~/Desktop/촉각비전_v3_정리_2026-10-03.txt`, `~/Desktop/촉각비전_프로젝트_정리_2026-10-02.txt` | |
| 실행 기록 | `~/tactile-vision/logs/` (`metrics_2026-10-05_*.csv` 등). `logs/metrics.csv`는 run.py가 매번 덮어씀 | |

**공개 저장소에 아직 안 올라간 변경 (젯슨 `~/tactile-vision`, 커밋 안 함)**

| 파일 | 내용 |
|---|---|
| `tools/render_sample_video.py` (새 파일) | 녹화 영상을 메인 코드로 처리해 4칸 비교 영상(H.264)과 CSV를 만듦 |
| `tools/render_all_samples.sh` (새 파일) | 원본 MOV 전체 → 바로 보는 MP4 변환 + 샘플 영상 일괄 처리 |
| `src/tactile_vision/pipeline.py` | `Pipeline(video_time=True)` 옵션 추가(영상 시간 기준 필터 dt). 기본 동작 불변, 시험 통과 |
| `README.md` | "샘플 영상" 절 추가 |

올릴지 사용자에게 먼저 물어볼 것. 올리면 논문 참고문헌 [30]의 커밋 해시(`632b1a1`)도 바꿔야 한다.

---

## 3. 장치 하드웨어 현재 상태 (2026-10-05 기준)

- **Jetson**: Orin Nano Super 개발자 키트 8 GB, `nvpmodel` 25 W, L4T R39, TensorRT 10.16.2, CUDA 13.2. 화면 `DISPLAY=:1`.
- **카메라**: Logitech C920 `/dev/video0`, 1280×720 MJPG 30 fps. 장치 코드가 열 때마다 자동초점 끄고 초점 0 고정.
- **Pico**: USB `2e8a:000a`, `/dev/ttyACM0`. **젯슨 USB-A 포트에 꽂을 것**(본체 USB-C는 장치 모드라 인식 안 됨). 권한: dialout 그룹 + udev 규칙 `tools/60-tactile-pico.rules` 적용됨.
- **I²C 배선**: **GP10 = SDA, GP7 = SCL** (둘 다 I2C1 → 펌웨어는 `Wire1`), 400 kHz. PCA9685 `0x40` = 1~2행, `0x41` = 3~4행(A0 납땜). 보드 안 채널: 1·3행 = 0 2 4 6 8 10, 2·4행 = 1 3 5 7 9 11 ("colpairs", 펌웨어 `tactile_core.h` `CELL_TO_CHANNEL` 한 곳에서 정의).
- **서보 전원**: 3S LiPo ×2 → 강압 컨버터 → 각 PCA9685 V+ (보드당 12개). 24개 동시 구동 허용.
- **서보 방향**: **역방향으로 조립됨** — tick이 클수록 핀이 내려감. 캘리브레이션 `calib/servo_calib.json` 24칸 모두 home(단계 0, 먼 곳, 핀 맨 아래) **372**, max(단계 7, 가까운 곳, 핀 맨 위) **232**. 단계 k = 372 − 20k tick, 한 단계 1.29 mm. 원래 기본값 백업: `calib/servo_calib_default_geometry_2026-09-22.json`.
- **펌웨어 v3** (`firmware/pico/tactile_pico/`, 올라가 있는 uf2 sha256 `3315a8a5d387537b…`):
  - 박자 200 ms마다 최신 GRID 적용, 5 ms마다 최대 4 tick 이동
  - 통신 0.5 s 끊김(failsafe) 또는 종료(HOME_ALL) → 모든 핀을 **10 ms마다 1 tick씩 천천히** 맨 아래(372)로, 끝→끝 약 1.4 s. ESTOP만 즉시
  - 켜질 때 기본 위치 372/232(이 장치 범위). Pico 전원 자체가 끊기면 서보가 힘을 잃음(소프트웨어로 못 막음)
- **Uno 호환 보드**(FTDI `/dev/ttyUSB0`, 빠져 있을 수 있음): 서보 1개 속도·범위 측정용 스윕 스케치 `firmware/calibration/uno_servo_sweep/`.

---

## 4. 실행법 (젯슨)

Python은 항상 `~/sensory_substitution/venv/bin/python -B` (venv에 torch·TensorRT 연동이 맞춰져 있음 — pip로 torch 재설치 금지).

```bash
cd ~/tactile-vision
PY=~/sensory_substitution/venv/bin/python

# 시험 (하드웨어 없이, 모두 통과 상태: 14/34/26/42/83 = 199항목)
for t in tools/test_mapping.py tools/test_protocol.py tools/test_scene.py tools/test_switch.py tools/test_firmware.py; do $PY -B $t | tail -1; done
$PY -B tools/test_switch.py --with-model     # 실제 엔진 사용 (GPU가 비어 있을 때만)

# 실전 실행 (카메라 + Pico + 확인 창). 핀이 움직임!
DISPLAY=:1 $PY -B run.py --debug             # 창에서 q 또는 Ctrl+C → 핀을 천천히 내리고 종료
$PY -B run.py --no-hw --duration 30          # Pico 없이
$PY -B run.py --show-mapping                 # 매핑 표 (주의: 8절 ⑤ — 표가 실제 양자화와 조금 다름)

# 백그라운드로 띄우고 끄기 (pgrep 패턴은 대괄호로 — 자기 자신을 잡지 않게)
DISPLAY=:1 setsid -f nohup $PY -B run.py --debug > /tmp/tv_run_live.log 2>&1 < /dev/null
kill -TERM $(pgrep -f '[r]un\.py --debug')

# 모터만 시험 (범위·방향은 캘리브레이션 파일을 따름)
$PY -B tools/servo_slow_updown.py --cycles 0   # 24개 함께 천천히 위아래, Ctrl+C로 멈추면 천천히 내려옴
$PY -B tools/servo_wave_test.py                # 채널 순서대로 파도 (배선 확인)
$PY -B tools/servo_updown_test.py              # 단계 0↔7 왕복
$PY -B tools/calibrate_pins.py                 # 채널별 home/max 보정 (대화형)

# 펌웨어 빌드·업로드 (도구는 tools/setup_firmware_toolchain.sh 로 설치됨)
tools/build_firmware.sh --upload /dev/ttyACM0  # run.py 등 포트를 쓰는 프로그램을 먼저 끌 것

# 녹화 영상 → 4칸 샘플 영상 (아직 공개 저장소에 없는 도구)
tools/render_all_samples.sh ~/Downloads/drive-download-20261005T105756Z-1-001
```

**논문 표·그림 다시 만들기**

```bash
cd ~/github/tactile-vision-thesis/thesis/analysis
~/sensory_substitution/venv/bin/python -B analyze.py      # data/*.csv → results.json, ../figures/v3/*.png
# make_example_data.py 는 예시 데이터 생성기(시드 고정). 실측 후에는 다시 돌리지 말 것(실측 CSV를 덮어씀).
```

docx/pdf 변환: `markdown==3.7`을 임시 폴더에 설치(`pip install --target /tmp/x`)해 md → HTML(그림 base64 내장) → `soffice --headless --convert-to 'docx:MS Word 2007 XML'` → `soffice --convert-to pdf`. 목차 줄 끝 공백 두 칸(줄바꿈)을 지울 것.

---

## 5. 사용자가 정한 것 (바꾸려면 물어볼 것)

- 깊이 입력 924×504, 애매한 장면에서는 모델 하나만(`uncertain_policy: hold`), Places365 초당 2회
- 위험 물체 YOLO26n, 진동 1/2/3°(자동차 등 3), 진동은 핀 갱신의 2배 빈도(초당 10회)
- 핀 갱신 초당 5회, 박자는 Pico가 정하고 젯슨은 결과가 나올 때마다 보냄
- 서보 24개 동시 구동
- 구동 범위 60°부터 140 tick (232~372 tick, 64.8°, 9.0 mm) — 박자 0.2 s 안에 끝→끝 이동
- 칸→채널 배열 colpairs, I²C GP10/GP7
- 역방향 조립은 소프트웨어 반전으로 처리, 끊김·종료 시 천천히 맨 아래로
- 코드 공개 저장소 MIT, 논문 저장소는 비공개 유지
- 시험 도구는 단순하게 (예: "모터 전부 천천히 위아래, 멈출 때까지 계속")

---

## 6. 작업 규칙 (사용자 선호)

1. 한국어로, 짧고 쉽게. 군더더기 없이. 끝나면 무엇을 했는지 몇 문장으로.
2. 권한은 sudo 포함 모두 허용되어 있지만, 지우기·덮어쓰기·되돌리기 어려운 일과 애매한 일은 먼저 확인.
3. **토큰·비밀번호 값은 절대 출력·저장하지 않는다.** 이전에 쓰던 GitHub 토큰은 교체(rotate)할 예정 — 새 도구는 자체 인증(`gh auth login` 등)을 쓸 것. `.git/config`에 자격 증명을 남기지 말 것.
4. git 커밋 이름은 `-c user.name=MuakTiger -c user.email=muaktiger@users.noreply.github.com` (git 설정 자체는 바꾸지 않음). 커밋·push는 사용자가 요청할 때. **공개 저장소 push는 반드시 물어보고.**
5. 논문 초안 v1·v2는 수정 금지. v3는 사용자가 요청할 때만 수정. 사실·결정·측정은 `FACTS.md`에 기록(표 셀 개수 맞는지 확인 — 45번째 줄은 원래부터 셀 안에 `\|`가 있어 예외).
6. 큰 작업이 끝나면 `~/Desktop/v3` 동기화(`rsync` 후 `diff -rq --exclude=__pycache__`로 확인)하고 FACTS.md에 기록·push.
7. 핀을 움직이는 명령(run.py, servo_*, 펌웨어 업로드)은 실행 전에 말할 것. 손이 패드 위에 있을 수 있음.
8. 젯슨 GPU·메모리(7.7 GB)가 빠듯하다. 모델을 쓰는 작업은 다른 모델 작업과 동시에 돌리지 말 것.
9. 사람 얼굴이 나오는 영상·사진은 공개 저장소에 올리지 않는다.

---

## 7. 지금까지의 흐름 (자세한 근거는 FACTS.md)

| 날짜 | 한 일 |
|---|---|
| 09-21~22 | v1 논문 초안(상대 깊이), 하드웨어·펌웨어 저장소 `tactile-vision-device`(커밋 `3f17469`) |
| 09-29 | metric 깊이 + 실내/실외 전환으로 v2 초안, 스마트폰 영상 예비 분석(실외/실내 거리 비 2.38~2.64배) |
| 10-01~02 | 젯슨 코드 확인, 카메라 C920 교체·초점 고정, 실내/실외 자동 전환을 run.py에 통합 |
| 10-03 | 924×504 엔진, YOLO26n, Pico 펌웨어 v3(박자 적용·진동·failsafe), 실측(15.3 fps, 14.5 W) |
| 10-04 | Pico 실기 연결·업로드, 권한, Uno 스윕 도구 |
| 10-05 | I²C GP10/GP7·Wire1, 채널 배열 colpairs, 서보 시험(오류 0), 범위 232~372 확정, `run.py --debug` 실전 구동, 역방향 조립 → 캘리브레이션 반전, 끊김·종료 시 천천히 내리기, 시험 도구 방향 수정, 코드 공개(MIT), 녹화 영상 14편 샘플 처리 |
| 10-06 | 논문 v3 초안(39쪽, 참고문헌 39개, 그림 8개) — 실험 1~3은 예시값 |

---

## 8. 남은 일 (우선순위 순)

1. **실험 1~3 실제 수행** → `thesis/analysis/data/*.csv`를 실측으로 교체 → `analyze.py` → 논문 본문 수치 교체 → 〔예시〕 표시와 맨 앞 작성 메모 삭제.
   - 실험 1 반응 시간: 240 fps 슬로모션, 0.5 m 판 출현/제거, 각 30회 (논문 3.2절)
   - 실험 2 핀 영점 편차: 디지털 깊이 게이지, 단계 0/7 × 10회, 보정 전후 (3.3절)
   - 실험 3 실내 10 m 보행: 눈가림 8명 × 3조건 × 3회 — **시작 전에 을지대 IRB 심의 필수**, 참여자 정보·승인번호 기입 (3.4절)
   - **예시값을 실측처럼 제출하면 연구부정(위조)이다.** 이 점을 계속 지킬 것.
2. **단계 수 결정 (FACTS S12)**: 한 단계 1.29 mm가 가정한 손바닥 구별 한계 2.5 mm보다 작음. 손바닥 높이 구별 역치를 재고 4~5단계로 줄일지 결정.
3. **채널별 캘리브레이션**: `tools/calibrate_pins.py`로 24칸 실측(지금은 24칸 공통 372/232). 영점과 스트로크 두 점 보정 검토.
4. **실외 모델 거리 과대 추정**: 녹화 영상에서 실외 판정 시 가까운 사람도 4 m 이상으로 나옴. 줄자·레이저로 실측해 모델별 배율 보정.
5. **코드 표시 불일치**: `run.py --show-mapping`의 단계별 거리표(`mapping.level_edges`, 8등분)가 실제 양자화(7·p 반올림)와 다름 — 실내 단계 7이 실제로는 0.50~0.58 m(표는 0.65 m). 논문은 실제 값 사용. 표를 실제 규칙에 맞게 고칠지 결정.
6. **하드웨어 확인**: 1° 진동이 실제로 움직이는지(SG90 데드밴드), 24개 동시 구동 전류·배선 발열, 서보 실제 속도(Uno 스윕 + 슬로모션).
7. **확인 화면 켠 상태의 실제 갱신률**: 약 9.4 fps(화면 없이 15.3 fps). 실험 1은 화면 없이 할 것.
8. **공개 저장소**: 2절의 미커밋 4개 파일을 올릴지 결정.
9. **논문 마무리**: 제출 연월·인준지 학과 양식, 참고문헌 원문 대조(특히 [4] Manduchi, [20] Weinstein 손바닥 값, [10] Grant), 실물 장치 사진 추가(지금 그림은 도식·그래프·처리 화면뿐).
10. **정리**: GitHub 토큰 교체, 예전 hooks 작업이 남긴 `~/.kiro/agents/tactile.json` 정리 여부.

---

## 9. 알아 두면 좋은 함정

- `pgrep -f 'run.py --debug'`처럼 쓰면 그 명령을 실행하는 셸 자신이 잡혀 죽는다 → `'[r]un\.py'`처럼 대괄호 패턴.
- `run.py`는 시작할 때마다 `logs/metrics.csv`를 덮어쓴다. 남길 실행은 날짜를 붙여 복사.
- 펌웨어 업로드·서보 도구 전에 Pico 포트를 쓰는 프로그램을 끌 것(`fuser /dev/ttyACM0`).
- 시험 도구 3개는 캘리브레이션 파일의 범위·방향을 따른다. 서보 방향을 다시 바꾸면 파일만 고치면 된다. 펌웨어 기동 기본값(`tactile_core.h` HOME/MAX_TICK_DEFAULT)과 `calibration.py` DEVICE_* 값도 함께 바꿀 것(`test_firmware.py`가 일치 검사).
- JetPack apt의 ffmpeg는 H.264 인코더가 없다. `~/.local/share/tv-ffmpeg`(imageio-ffmpeg 0.6.0 정적 ffmpeg)를 쓴다.
- 아이폰 영상은 HDR(HLG)이라 OpenCV로 바로 읽으면 색이 바랜다 → 변환된 MP4를 입력으로.
