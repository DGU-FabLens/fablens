# FabLens 데이터 품질 리포트

> 1주차 산출물. PHM 2016 CMP training 데이터의 품질을 한 문서로 정리합니다.
> 모든 수치는 `scripts/01_profile_raw.py`와 `scripts/03_build_features.py` 실행
> 결과이며, 이후 모든 단계의 **검증 기준값**입니다.
>
> 재현: `.venv/bin/python scripts/01_profile_raw.py`

## 1. 요약

| 항목 | 값 | 판정 |
|---|---|---|
| trace row | 672,744 | — |
| trace 파일 | 185개 중 184개 로드 (빈 파일 1개) | ✅ 정상 |
| 고유 wafer-stage | 1,981 | ✅ 라벨과 1:1 |
| 결측 | 원본 25개 컬럼 **전부 0건** | ✅ 처리 불필요 |
| Join 누락 | 0건 | ✅ |
| 타깃 이상치 | 4건 (>1000) → 제거 | ✅ 제거 후 1,977 |
| 상수 컬럼 | `MACHINE_ID` 1개 | ✅ feature 제외 |

## 2. 결측

원본 25개 컬럼 전부 결측 **0건**. 결측 처리(imputation) 불필요
(`04_TECHNICAL_DECISIONS` 종료 항목). 빈 파일 `CMP-training-066.csv`는 헤더 전용
빈 원본으로, 원본 보존을 위해 삭제하지 않고 로드 시 건너뜁니다.

## 3. 상수 · 저분산 컬럼

- **완전 상수:** `MACHINE_ID` (값 2 하나) → feature 제외 (DL-20260720-003).
- **집계 후 상수:** 여러 압력 센서의 `_min`이 전 wafer-stage에서 0으로 동일해
  Feature Table 생성 시 상수로 제거됨 (9개):
  `PRESSURIZED_CHAMBER_PRESSURE_min`, `MAIN_OUTER_AIR_BAG_PRESSURE_min`,
  `CENTER_AIR_BAG_PRESSURE_min`, `RETAINER_RING_PRESSURE_min`,
  `RIPPLE_AIR_BAG_PRESSURE_min`, `EDGE_AIR_BAG_PRESSURE_min`,
  `SLURRY_FLOW_LINE_C_min`, `WAFER_ROTATION_min`, `STAGE_ROTATION_min`.
  → 센서가 매 wafer-stage 0에서 시작함을 의미(측정 시작점).

## 4. 타깃 이상치

규칙 `AVG_REMOVAL_RATE > 1000` → **4건 제거** (DL-20260720-003). 물리적으로 불가능한
값이며, 제외 후 다음으로 큰 값은 162.6. 전부 STAGE A / chamber_group G123.

| WAFER_ID | STAGE | group | AVG_REMOVAL_RATE |
|---|---|---|---|
| 2058207580 | A | G123 | 4326.15 |
| 1834206730 | A | G123 | 4202.11 |
| 1834206944 | A | G123 | 4182.42 |
| 1834206972 | A | G123 | 4129.49 |

**제외 건수가 4가 아니면 파이프라인 중단하고 원인 확인** (config/features.yaml).

## 5. Join 정합성

| _merge | 건수 |
|---|---|
| both | 1,981 |
| left_only (센서만) | 0 |
| right_only (라벨만) | 0 |

→ 모든 wafer-stage가 센서·라벨을 모두 가짐. **Join 누락 0건.**

## 6. 그룹 단위 이상치 (미처리, 모니터링 대상)

wafer-stage별 row 수와 공정시간에 **긴 꼬리**가 존재합니다.

| 지표 | STAGE A | STAGE B |
|---|---|---|
| n_rows 중앙값 | 338 | 347 |
| n_rows 최대 | 821 | **5,492** |
| duration 중앙값(초) | 356 | 364 |
| duration 최대(초) | **29,311** | 5,567 |

- duration 29,311초(약 8시간)짜리 wafer-stage가 train 구간에 존재.
- slope/duration 계열 feature가 이 샘플에서 튈 수 있어 **그룹 단위 이상치 처리는
  후속 단계 미확정 항목**(`04_TECHNICAL_DECISIONS`). 시간순 split 분리에는 영향 없음.

## 7. 조건별 타깃 분포 (이상치 제거 후 1,977건)

| STAGE | chamber_group | count | mean | std |
|---|---|---|---|---|
| A | G123 | 364 | 151.24 | 3.90 |
| A | G456 | 798 | 73.08 | 6.65 |
| B | G456 | 815 | 79.97 | 9.15 |

- MRR이 **이봉분포**이며 `chamber_group`으로 대부분 갈림(G123 ~151 / G456 ~73~80).
- `CHAMBER`가 wafer-stage 안에서 변하는 경우 1,979 / 1,981건 → 계열 구분이
  Stage A의 이봉분포를 설명 (DL-20260720-002).
- **주의:** 조건 변수가 이봉분포를 설명하므로 전체 R²는 부풀 수 있음. 모델 평가 시
  그룹 내부 지표를 함께 볼 것.

## 8. 품질 판정

원본 데이터는 **결측 0 / Join 누락 0 / 상수·이상치 식별 완료**로 모델링 진입에
적합합니다. 남은 관리 대상은 그룹 단위 길이 이상치(6절)와 `MACHINE_DATA` 역할
확정(§컬럼 Dictionary 5절)입니다.
