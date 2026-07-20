# FabLens 팀 간 데이터 계약 (Data Contract)

> **공통 문서입니다.** 김민지(Data & ML)가 생성하고 강민수(Decision & System)가 소비하는
> 중간 산출물의 형식을 고정합니다. 여기 적힌 컬럼명·경로가 바뀌면 양쪽 코드가 함께
> 깨지므로, 변경 시 팀에 공유하고 `docs/decisions/`에 기록합니다.
>
> 경로는 모두 `config/paths.yaml`에 정의되어 있습니다. 코드에 직접 적지 않습니다.

---

## 1. 산출물 소유권

| 산출물 | 경로 키 (`paths.yaml`) | 생성 | 소비 |
|---|---|---|---|
| 원본 프로파일 | `reports.data_profile` | 공통 (`01_profile_raw.py`) | 전원 |
| Feature Table | `processed.feature_table` | 김민지 | 강민수 (SPC·Dashboard) |
| Split Manifest | `processed.split_manifest` | 김민지 | 강민수 (Phase I/II 경계) |
| 예측 결과 | `artifacts.predictions` | 김민지 | 강민수 |
| 성능 지표 | `artifacts.metrics` | 김민지 | 강민수 (Dashboard) |
| SHAP 값 | `artifacts.shap` | 김민지 | 강민수 (Dashboard 상세 화면) |
| 데이터 품질 Flag | 미정 | 강민수 | Rule Engine, Dashboard |

---

## 2. 확정된 공통 사실 (`scripts/01_profile_raw.py` 결과)

이 숫자들은 양쪽 코드의 검증 기준값입니다.

| 항목 | 값 |
|---|---|
| trace row 수 | 672,744 |
| 고유 wafer-stage | **1,981** (라벨과 1:1, 누락 0건) |
| 결측 | 원본 25개 컬럼 **전부 0건** |
| 타깃 이상치 제외 후 | **1,977** (DL-20260720-003) |
| 조건 구분 | `STAGE` (A 1,166 / B 815), `chamber_group` (G123 368 / G456 1,613) |

---

## 3. 공통 키와 명명 규칙 (변경 금지)

```
분석 단위 키 : (WAFER_ID, STAGE)      ← 두 컬럼 조합이 유일 식별자
시간 정렬 기준: first_ts               ← 그룹 최초 TIMESTAMP. 중복 0건 확인
순번          : order_index            ← first_ts 오름차순, 0부터
타깃          : AVG_REMOVAL_RATE
조건 변수     : STAGE, chamber_group   ← chamber_group은 "G123" / "G456" 문자열
```

**Feature 컬럼 명명: `{원본컬럼명}_{집계함수}`**
예: `SLURRY_FLOW_LINE_A_mean`. SHAP 결과에서 센서를 역추적해야 하므로 원본 컬럼명을
축약하지 않습니다 (`02_AI_DEVELOPMENT_RULES` 7장).

---

## 4. Feature Table 스키마

**행 단위: wafer-stage 1건**

| 컬럼 | 타입 | 구분 |
|---|---|---|
| `WAFER_ID` | int64 | key |
| `STAGE` | str (`A`/`B`) | key / 조건 변수 |
| `chamber_group` | str (`G123`/`G456`) | 조건 변수 |
| `first_ts`, `last_ts` | float | metadata (정렬·SPC 경계용) |
| `order_index` | int | metadata |
| `AVG_REMOVAL_RATE` | float | 타깃 |
| 그 외 numeric 컬럼 | float | 모델 Feature |

**Feature 목록은 `data/processed/feature_schema.json`에 함께 저장합니다.**
강민수 쪽 코드는 이 JSON의 `feature_columns`를 읽어야 하며, 컬럼명을 하드코딩하지
않습니다.

```json
{
  "n_rows": 0,
  "keys": ["WAFER_ID", "STAGE"],
  "meta_columns": [...],
  "condition_columns": ["STAGE", "chamber_group"],
  "feature_columns": [...],
  "n_features": 0
}
```

---

## 5. Split Manifest 스키마

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `WAFER_ID` | int64 | key |
| `STAGE` | str | key |
| `first_ts` | float | 정렬 기준 |
| `order_index` | int | 시간순 순번 |
| `split` | str | `train` / `validation` / `test` / **`buffer`** |

**불변 조건**

- 동일 `(WAFER_ID, STAGE)`는 정확히 한 번만 등장합니다.
- `train` → `validation` → `test` 구간의 시간 범위가 서로 겹치지 않습니다.
- 경계에서 시간이 겹치는 샘플은 `buffer`로 표시하고 학습·평가 어디에도 쓰지
  않습니다 (DL-20260720-005).

**SPC와의 연결**: 강민수의 Phase I 기준 구간은 이 manifest의 `train` 구간과 동일하게
잡습니다. `validation` 포함 여부는 아래 미확정 항목.

---

## 6. 예측 결과 스키마

| 컬럼 | 설명 |
|---|---|
| `WAFER_ID`, `STAGE` | key |
| `order_index` | 시간순 순번 |
| `y_true` | 실제 MRR — **오프라인 평가 전용. Rule Engine 입력 금지** |
| `y_pred` | 예측 MRR |
| `model_name` | 모델 식별자 |
| `experiment_id` | 실험 ID (결과 덮어쓰기 방지, TD-010) |

`y_true`가 파일에 함께 들어 있어도 실시간 판정 경로에서는 절대 참조하지 않습니다
(`01_PROJECT_SOURCE_OF_TRUTH` 7장).

---

## 7. 합의 필요 항목

- [ ] Phase I 구간 = `train`인지 `train`+`validation`인지
- [ ] split buffer 폭 (DL-20260720-005에서 미정)
- [ ] `experiment_id` 생성 규칙 (timestamp vs 수동 지정)
- [ ] 데이터 품질 Flag 컬럼명과 값 정의 (강민수 설계)
- [ ] Dashboard가 parquet을 직접 읽을지, 별도 요약 CSV를 받을지
