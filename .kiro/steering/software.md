---
inclusion: fileMatch
fileMatchPattern: 'device*/**'
---

# 소프트웨어 세션 작업 규약

## 어느 저장소인가를 항상 먼저 확정한다

`device/`(논문 기준, `3f17469`)와 `device-dev/`(YOLO 확장, `fd289e6`)는 별개 리모트다.
수정 요청을 받으면 **어느 쪽인지 먼저 확인**한다. 추측해서 고르지 않는다.

- 논문에 인용되는 동작을 바꾸는 수정 → `device/`. 변경 시 `FACTS.md`에 영향 범위를 기록해 논문 세션이 알 수 있게 한다.
- YOLO·위험도·jittering 관련 → `device-dev/`
- `device-dev/`에는 미커밋 파일이 있다 (`software/pico/main_pico_v3.cpp`, `skku_sagemaker.html`). 커밋 여부를 사용자에게 확인한다.

## 구성

| 파일 | 역할 |
|---|---|
| `software/main.py` | Jetson 메인 파이프라인. TensorRT 추론 → 24구역 평균 → 시리얼 송신 |
| `software/pico/main.cpp` | Pico 펌웨어. 패킷 파싱 → PCA9685 ×2 → SG90 ×24 |
| `software/requirements.txt` | `device/`에만 존재 |
| `hardware/parts|assembly|full/*.stl` | `device/`에만 존재 |
| `scripts/HANDOFF_ORIN.md` | Jetson 배포 인수인계 문서 |

실행:
```bash
python software/main.py                 # 기본
python software/main.py --debug         # 시각화 창
python software/main.py --no-hw --debug # 하드웨어 없이
python software/main.py --port /dev/ttyACM1 --debug
```

## 하드웨어 없는 환경에서의 검증

이 맥은 Jetson도 Pico도 아니다. TensorRT·serial·PCA9685에 의존하는 경로는 여기서 실행할 수 없다.
따라서:

- 파이썬 수정은 `--no-hw`로 확인 가능한 범위까지만 검증하고, **실기 검증이 남았음을 명시**한다.
- Pico C++은 컴파일조차 불가하므로 정적 검토에 그친다. "동작 확인됨"이라고 쓰지 않는다.
- 검증하지 못한 것을 검증했다고 보고하지 않는다.

## 알려진 이슈 (논문 §3.3.3, §6.3에서 지적된 것)

1. **USB CDC 보드레이트 오기** — 코드/README는 115200 bps로 기술하지만 `/dev/ttyACM0` + arduino-pico `Serial`은 USB CDC-ACM이라 보드레이트가 무시된다. 실효 대역은 USB FS 12 Mbps. 주석·문서 정정 대상.
2. **패킷 무결성 없음** — 체크섬·시퀀스 번호가 없다. 펌웨어는 토큰 24개 여부만 검증하므로 값이 손상된 패킷도 서보에 인가된다. 하드웨어 UART 전환 시 체크섬 필수.
3. **I2C 100 kHz 병목** — `setPWM` 24회가 12.96 ms(30 fps 예산의 39%)*(산정치)*. `Wire.setClock(400000)`으로 3.24 ms 예상. 한 줄 수정.
4. **`SAFE_MAX` 마진 부족** — 490 tick은 179.3°*(산정치)* 로 SG90 정격 상한에 근접. 조립 공차에 따라 기계적 스톱과 충돌 가능.

이 항목들을 수정하면 논문의 해당 절과 *(산정치)* 가 영향을 받는다. **반드시 `FACTS.md`에 기록**한다.

## 실측이 나왔을 때

논문은 지연 예산(L5/L7/L8), FPS, 전원 사양을 *(산정치)* 로 두고 실측 대기 중이다.
벤치에서 숫자가 나오면 즉시 `FACTS.md` 확정 사실에 등재한다. 측정 조건(장비, 반복 횟수,
커밋 해시)을 함께 적어야 논문 세션이 근거로 인용할 수 있다.

## 코드 스타일

- 기존 파일의 컨벤션을 따른다. 한글 주석 + 박스형 구분선(`# ───`)이 현재 스타일이다.
- 상수는 파일 상단에 대문자로 모아 둔다 (`DANGER_MAP`, `SAFE_MAX` 등).
- 요청되지 않은 리팩터링·의존성 추가를 하지 않는다. 임베디드 타깃이라 의존성 비용이 크다.
