# FabLens 팀 역할 및 4주 WBS

## 1. 역할 설계 원칙

- 역할은 문서 조사만 하는 사람과 코드만 쓰는 사람으로 분리하지 않습니다.
- 각 팀원에게 독립적으로 설명 가능한 구현 산출물이 있어야 합니다.
- 전원이 데이터 구조, MRR, VM, SPC의 기본 원리를 이해합니다.
- 통합 단계는 특정 한 명에게 마지막에 몰지 않고 매주 연결합니다.

---

## 2. 민수 권장 역할

### 역할명

**SPC·품질 의사결정 및 시스템 통합 담당**

### 직접 담당

- 데이터 품질 판정 규칙
- Phase I·II 기반 SPC 흐름
- Shewhart 관리도
- 정상·주의·계측 권장 Rule Engine
- 계측 정책 평가
- Streamlit Dashboard
- 모델 산출물과 UI 연결
- 통합 테스트와 시연 흐름

### 공동 참여

- 원본 데이터 구조 확인
- Feature 정의 리뷰
- 시간순 Split 검토
- 모델 결과 해석
- SHAP 화면 연결

### 역할 선택 이유

민수는 기존 프로젝트에서 다음 경험이 있습니다.

- 센서 정상 범위와 예외 처리 설계
- 시계열·센서 데이터 신뢰성 확인
- 입력 이상과 시스템 상태 관리
- FastAPI·DB·WebSocket·화면 통합
- 테스트 시 JSON, DB, 화면 상태를 함께 검증

따라서 순수 모델 성능 경쟁보다, 분석 결과를 품질 판단과 시스템 흐름으로 연결하는 역할이 기존 경험과 신규 반도체 역량을 동시에 보여주기 좋습니다.

---

## 3. 2인 역할 분담

### A. 데이터·Virtual Metrology 담당

- 데이터 확보와 구조 분석
- wafer-stage Join
- 전처리
- Feature Engineering
- 시간순 Split
- 선형·RF·GBDT 모델
- 성능 평가
- SHAP 계산 코드

### B. 민수 — SPC·의사결정·Dashboard 담당

- 데이터 품질 Flag
- SPC 기준 구간 설계
- 관리한계와 경보
- Rule-based 계측 우선순위
- 계측 정책 평가
- Dashboard
- 전체 통합과 테스트

### 공동 책임

- 공정 용어 조사
- Feature 의미 검토
- 모델 선택
- 결과 해석
- README·발표
- 면접 예상 질문 준비

---

## 4. 3인 역할 분담

### A. 공정·데이터 담당

- CMP·MRR·pad·dresser·Stage 조사
- 데이터 Dictionary
- Join 정합성
- 전처리
- Feature 후보와 공정 해석
- 모델 결과의 도메인 검토

단순 조사 역할로 끝내지 않고 전처리 코드와 Feature 정의 파일을 직접 담당합니다.

### B. 데이터·Virtual Metrology 담당

- 모델 입력 Dataset
- 시간순 Split
- 모델 세 가지 비교
- Hyperparameter 제한 탐색
- 성능표
- SHAP 계산

### C. 민수 — SPC·품질 의사결정·통합 담당

- 데이터 품질 Rule
- SPC
- 계측 우선순위
- 정책 비교
- Streamlit
- 통합 테스트
- 데모 시나리오

---

## 5. 4주 WBS

### 1주차 — 데이터 구조를 확정합니다

#### 목표

원본 데이터를 wafer-stage 학습 테이블로 재생성할 수 있어야 합니다.

#### 필수 산출물

- 원본 파일 목록
- Dataset Profile
- 컬럼 Dictionary
- wafer-stage Join 결과
- 시간 정렬 기준
- 전처리 스크립트
- 데이터 품질 리포트

#### 종료 조건

- 타깃 Join 누락 수를 설명할 수 있습니다.
- 한 wafer-stage의 모든 row가 함께 처리됩니다.
- 사용·제외 컬럼의 이유가 기록됩니다.

---

### 2주차 — Virtual Metrology Baseline을 완성합니다

#### 목표

세 모델의 시간순 검증 성능을 재현할 수 있어야 합니다.

#### 필수 산출물

- Feature Table
- Split Manifest
- 선형 Baseline
- Random Forest
- XGBoost 또는 LightGBM
- MAE·RMSE·R² 비교표
- 실제값–예측값 그래프

#### 종료 조건

- 같은 명령으로 실험이 재실행됩니다.
- 랜덤 Split과 시간순 Split 차이를 설명할 수 있습니다.
- 대표 모델 선택 근거가 있습니다.

---

### 3주차 — SPC와 계측 의사결정을 완성합니다

#### 목표

예측값이 품질 상태와 계측 추천으로 연결돼야 합니다.

#### 필수 산출물

- Phase I 기준선
- Phase II 관리도
- Rule Engine
- 계측 권장 목록
- SHAP 개별 설명
- 정책 평가 초안

#### 종료 조건

- 실제 holdout MRR 없이 추천 결과가 생성됩니다.
- 추천 사유가 코드와 화면에서 동일합니다.
- SHAP를 원인 후보로 설명합니다.

---

### 4주차 — 시연 가능한 제품 형태로 통합합니다

#### 목표

새 환경에서 실행 가능한 Dashboard와 문서를 완성합니다.

#### 필수 산출물

- Streamlit Dashboard
- 최종 결과 테이블
- README
- 분석 보고서
- 발표 자료
- 3~5분 데모
- 한계와 후속 계획

#### 종료 조건

- 처음 보는 사람이 README만 보고 실행할 수 있습니다.
- 주요 화면에서 특정 wafer-stage의 판정 근거를 추적할 수 있습니다.
- 모든 수치가 결과 파일에서 재확인됩니다.

---

## 6. 기능 삭제 순서

일정이 밀리면 다음 순서로 제거합니다.

1. Conformal·OOD·Adaptive SPC 등 애초 제외 기능
2. Ensemble 불확실성
3. CUSUM
4. EWMA
5. Recipe별 SPC
6. 복잡한 Trade-off
7. Dashboard 장식 요소

다음은 삭제하지 않습니다.

- 전처리 정합성
- Feature Table
- 시간순 검증
- 기본 VM 모델
- 기본 SPC
- Rule-based 계측 우선순위
- 최소 Dashboard
- 결과 재현성
