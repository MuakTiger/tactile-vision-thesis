# 장치 코드 재현 확인 (`device_ground_check.py`, tactile-vision-ground, TensorRT FP16)

- outdoor site1 (n=30): ground 장치 MAPE 10.8% / 분석 10.9% (사진별 차 중앙 0.11%, 최대 0.3%); metric_b 장치 MAPE 6.7% / 분석 6.7% (사진별 차 중앙 0.00%, 최대 0.0%);
- outdoor site2 (n=30): ground 장치 MAPE 31.3% / 분석 31.2% (사진별 차 중앙 0.13%, 최대 0.4%); metric_b 장치 MAPE 69.3% / 분석 69.3% (사진별 차 중앙 0.00%, 최대 0.0%);
- outdoor 합침 (n=60): ground 장치 MAPE 21.1% / 분석 21.1% (사진별 차 중앙 0.12%, 최대 0.4%); metric_b 장치 MAPE 38.0% / 분석 38.0% (사진별 차 중앙 0.00%, 최대 0.0%);
- indoor site1 (n=30): ground 장치 MAPE 51.9% / 분석 52.0% (사진별 차 중앙 0.11%, 최대 0.9%); metric_b 장치 MAPE 10.1% / 분석 10.1% (사진별 차 중앙 0.00%, 최대 0.0%);
- indoor site2 (n=30): ground 장치 MAPE 57.6% / 분석 57.6% (사진별 차 중앙 0.13%, 최대 1.3%); metric_b 장치 MAPE 7.9% / 분석 7.9% (사진별 차 중앙 0.00%, 최대 0.0%);
- indoor 합침 (n=60): ground 장치 MAPE 54.8% / 분석 54.8% (사진별 차 중앙 0.13%, 최대 1.3%); metric_b 장치 MAPE 9.0% / 분석 9.0% (사진별 차 중앙 0.00%, 최대 0.0%);
