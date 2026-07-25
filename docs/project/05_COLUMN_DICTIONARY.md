# FabLens 컬럼 Dictionary

> 1주차 산출물. PHM 2016 CMP training 데이터의 컬럼별 타입·역할·값 범위를 정리합니다.
>
> **원칙:** 데이터에서 **확인된 사실만** 적습니다. 컬럼 "의미"는 원본 명칭 기반
> 해석이며 물리 단위·정의는 공개 데이터에 명세가 없어 **미확인**으로 둡니다
> (`01_PROJECT_SOURCE_OF_TRUTH` 3장: 컬럼 의미를 추측해 확정하지 않음).
>
> 값 범위는 trace 672,744 row 기준(`scripts/01_profile_raw.py`,
> `scripts/03_build_features.py` 검증). 역할 근거는 `config/features.yaml`,
> `docs/project/04_TECHNICAL_DECISIONS.md`, `docs/decisions/02_DECISION_LOG.md`.

## 1. 키 · 타깃 · 조건 · 메타

| 컬럼 | 타입 | 역할 | 값 | 명칭 기반 해석 | 비고 |
|---|---|---|---|---|---|
| `WAFER_ID` | int64 | **키** | 고유 1,699 | 웨이퍼 식별자 | `STAGE`와 조합해 wafer-stage 유일 식별 (TD-001) |
| `STAGE` | str | **키 + 조건** | A / B | 공정 단계 | A 1,166 / B 815 |
| `AVG_REMOVAL_RATE` | float | **타깃** | 라벨 파일 | 평균 제거율(MRR 품질값) | `CMP-training-removalrate.csv`에 wafer-stage당 1값 |
| `TIMESTAMP` | float | **메타(정렬)** | 초 단위 float | 상대 시각 | 절대 시각 아님. **순서 정렬에만** 사용 |
| `CHAMBER` | float | **조건 소스** | 1~6 | 챔버 번호 | wafer-stage 안에서 1→2→3 또는 4→5→6으로 변함. `chamber_group` 파생 (DL-20260720-002) |
| `chamber_group` | str(파생) | **조건** | G123 / G456 | CHAMBER 계열 | G123 368 / G456 1,613. 물리 의미 미확인, 관측된 구분자로만 사용 |

## 2. 제외 · 미확정

| 컬럼 | 타입 | 역할 | 값 | 비고 |
|---|---|---|---|---|
| `MACHINE_ID` | int64 | **제외(상수)** | 2 하나뿐 | 전 row 동일값 → feature 제외 (DL-20260720-003) |
| `MACHINE_DATA` | int64 | **미확정** | 1~6 (6종) | 의미 미확인. **값 범위가 `CHAMBER`(1~6)와 동일** → 연관 가설, EDA 후 feature/metadata 판정 |
| `source_file` | str | 추적용 | 184 파일명 | 로더가 추가한 컬럼(원본 아님). 파일=웨이퍼가 아니므로 식별자로 쓰지 않음 |

## 3. 센서 Feature 후보 (19개)

값 범위는 row 단위 min~max. **역할: 모델 feature 후보** (wafer-stage 단위로 집계, TD-003).

### 소모품 사용량 (usage)

| 컬럼 | min | mean | max | 명칭 기반 해석 |
|---|---|---|---|---|
| `USAGE_OF_BACKING_FILM` | 19.2 | 4968.5 | 10532.5 | backing film 사용량 |
| `USAGE_OF_DRESSER` | 5.2 | 396.4 | 771.9 | dresser 사용량 |
| `USAGE_OF_POLISHING_TABLE` | 0.0 | 172.0 | 357.0 | polishing table 사용량 |
| `USAGE_OF_DRESSER_TABLE` | 2664.8 | 3496.4 | 4305.5 | dresser table 사용량 |
| `USAGE_OF_MEMBRANE` | 0.2 | 58.9 | 124.9 | membrane 사용량 |
| `USAGE_OF_PRESSURIZED_SHEET` | 5.8 | 1490.6 | 3159.8 | pressurized sheet 사용량 |

### 압력 (pressure)

| 컬럼 | min | mean | max | 명칭 기반 해석 |
|---|---|---|---|---|
| `PRESSURIZED_CHAMBER_PRESSURE` | 0.0 | 50.0 | 189.1 | 가압 챔버 압력 |
| `MAIN_OUTER_AIR_BAG_PRESSURE` | 0.0 | 155.3 | 499.2 | 헤드 main/outer 에어백 압력 |
| `CENTER_AIR_BAG_PRESSURE` | 0.0 | 40.2 | 139.4 | center 에어백 압력 |
| `RETAINER_RING_PRESSURE` | 0.0 | 1218.8 | 10662.6 | retainer ring 압력 |
| `RIPPLE_AIR_BAG_PRESSURE` | 0.0 | 6.0 | 22.5 | ripple 에어백 압력 |
| `EDGE_AIR_BAG_PRESSURE` | 0.0 | 28.5 | 141.5 | edge 에어백 압력 |

### 슬러리 유량 (slurry)

| 컬럼 | min | mean | max | 명칭 기반 해석 |
|---|---|---|---|---|
| `SLURRY_FLOW_LINE_A` | 0.0 | 4.3 | 42.6 | 슬러리 A 라인 유량 |
| `SLURRY_FLOW_LINE_B` | 0.0 | 0.7 | 12.5 | 슬러리 B 라인 유량 |
| `SLURRY_FLOW_LINE_C` | 0.0 | 249.4 | 1083.6 | 슬러리 C 라인 유량 |

### 회전 (rotation)

| 컬럼 | min | mean | max | 명칭 기반 해석 |
|---|---|---|---|---|
| `WAFER_ROTATION` | 0.0 | 12.8 | 34.9 | 웨이퍼 회전 |
| `STAGE_ROTATION` | 0.0 | 52.4 | 263.6 | stage(platen) 회전 |
| `HEAD_ROTATION` | 0.0 | 159.8 | 192.0 | 헤드 회전 |

### 상태 (status)

| 컬럼 | min | mean | max | 명칭 기반 해석 |
|---|---|---|---|---|
| `DRESSING_WATER_STATUS` | 0.0 | 0.42 | 1.0 | dressing water on/off (이진) |

## 4. 집계 후 Feature 컬럼

위 19개 센서를 wafer-stage 단위로 집계해 `{원본컬럼}_{집계함수}` 형식의 feature를
만듭니다 (mean/std/min/max/range/slope/delta). 상수·고상관 제거 후 **최종 59개**.
전체 목록은 `data/processed/feature_schema.json`의 `feature_columns`를 참조합니다
(강민수 쪽 코드는 컬럼명을 하드코딩하지 않고 이 JSON을 읽음, 데이터 계약 §4).

## 5. 확인이 필요한 항목

- `MACHINE_DATA` 역할 (feature / metadata) — CHAMBER와의 관계 확인 후
- `CHAMBER` / `chamber_group`의 물리적 의미 — 현재는 관측된 그룹 구분자로만 사용
- 센서 값의 물리 단위 — 공개 데이터에 명세 없음
