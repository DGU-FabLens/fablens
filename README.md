# FabLens

FabLens는 PHM 2016 CMP 공정 센서 시계열을 wafer-stage 단위로 가공해 Material
Removal Rate(MRR)를 예측하고, 기본 SPC와 규칙 기반 판정으로 추가 계측이 필요한
대상을 추천하는 품질 의사결정 플랫폼을 목표로 합니다.

## 해결하려는 문제와 계획된 파이프라인

공개 CMP 데이터에서 센서 정보로 MRR을 예측하고, 예측 결과와 통계적 공정 상태를
바탕으로 추가 확인 대상을 설명 가능한 기준으로 선별할 수 있는지 제한적으로
검증합니다.

계획된 흐름은 원본 구조·정합성 검사, wafer-stage 집계, Feature Engineering,
시간순 train/validation/test 분할, Virtual Metrology 회귀 모델 비교, Phase I 기준의
기본 SPC, SHAP 원인 후보 분석, 규칙 기반 계측 우선순위, Streamlit Dashboard입니다.

## 현재 상태

완료된 내용은 프로젝트 기획 문서 정리, PHM 2016 CMP training 데이터 확보, 기본
데이터셋 폴더 구성 확인입니다. 현재는 2인 협업을 위한 저장소와 Python 패키지의
기본 구조를 초기화한 단계입니다.

데이터 로더, 자동 데이터 검증, wafer-stage Feature Table, 시간순 분할, Virtual
Metrology 모델, SPC, SHAP, 계측 우선순위 및 Dashboard는 아직 구현되지 않았으며
향후 개발할 예정입니다.

## 데이터와 분석 단위

- 데이터셋: PHM 2016 CMP Data Challenge 공개 training 데이터
- 목표값: `AVG_REMOVAL_RATE`(프로젝트 내 MRR 품질값)
- 기본 분석 단위: 원본 row가 아닌 wafer-stage
- 동일 wafer-stage의 시계열은 하나의 데이터 분할에만 포함

원본 데이터는 `data/raw/phm2016_cmp/`에 있습니다. `CMP-training-066.csv`는 알려진
헤더 전용 빈 원본 파일이며, 원본 보존을 위해 삭제하지 않습니다.

## 저장소 구조

```text
config/                 설정 파일
data/                   raw, interim, processed 데이터
src/fablens/            Python 패키지
scripts/                실행 스크립트
tests/                  테스트
notebooks/              탐색용 노트북
experiments/            실험 정의
artifacts/              모델·예측·지표·그림·SHAP 결과
reports/                데이터 및 실험 보고서
docs/                   프로젝트 기준·결정·참고·연구 문서
```

## Python 환경

Python 3.11 이상을 사용합니다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

현재 의존성은 초기 구조에 필요한 최소 수준으로 제한되어 있습니다.

## 기준 문서

작업 전 `docs/project/01_PROJECT_SOURCE_OF_TRUTH.md`,
`docs/project/02_AI_DEVELOPMENT_RULES.md`, `docs/project/03_TEAM_ROLES_AND_WBS.md`,
`docs/project/04_TECHNICAL_DECISIONS.md`를 확인합니다. 연구 배경과 공식 출처는
`docs/research/`와 `docs/references/`에 있으며, 결정 변경은 `docs/decisions/`의
템플릿으로 기록합니다.

## 데이터 보존과 프로젝트 한계

`data/raw/`는 수정하지 않는 원본 영역입니다. 원본 CSV와 생성 데이터·결과물은
일반 Git 추적 대상에서 제외하며, 문서와 출처·라이선스 파일은 추적할 수 있습니다.

이 프로젝트는 공개 데이터 기반의 의사결정 보조 실험입니다. 실제 Fab 검증, 제품
규격 판정, 불량 원인 확정, 검사 대체, 수율 개선 또는 비용 절감 효과를 주장하지
않습니다. SPC 관리한계는 제품 규격이 아니며 SHAP는 인과관계를 증명하지 않습니다.

## 다음 단계

1. 원본 데이터 자동 검증
2. wafer-stage profiling
3. Feature Schema 결정

## 👥 Team

### 👨 강민수 | Decision & System

- SPC(Shewhart Control Chart) 구현
- Rule-based Inspection Recommendation 구현
- Inspection Ratio–Detection Rate Trade-off 분석
- Streamlit Dashboard 개발 및 전체 시스템 통합

### 👩 김민지 | Data & ML

- CMP 센서 데이터 전처리 및 Feature Engineering
- Virtual Metrology(MRR Prediction) 모델 개발
- Time-aware Validation을 통한 모델 성능 평가
- SHAP 기반 예측 결과 설명 및 원인 후보 분석