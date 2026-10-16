# 거리 정확도 — 실외 원본 사진 (2026-10-16)

- 촬영: 2026-10-16 18:01~18:05, 노트북(Windows)에 연결한 장치의 Logitech C920, 1280×720 PNG(무손실, 덧그림 없음), 자동초점 끔·초점 0(장치 설정과 같음)
- 촬영 도구: 노트북의 `distance_capture/capture.py` (연산 없이 저장만)
- 거리: 줄자로 잰 렌즈~물체 거리 1·2·3·4·6·8 m, 거리마다 1장. 실제 거리는 파일 이름과 `shots.csv`의 `distance_m`
- 물체: 작은 상자(계획한 50×70 cm 판 아님). 1 m 사진은 상자가 화면 아래 끝에 걸림. 6·8 m는 상자가 아주 작다
- 카메라는 6장 내내 같은 자리(배경 동일)

젯슨에서 추정:

    cd ~/tactile-vision && python tools/compare_models.py --source ~/github/tactile-vision-thesis/thesis/analysis/data/raw/distance_outdoor_20261016
