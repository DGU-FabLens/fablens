# FabLens 공식 참고 자료

이 문서는 `deep-research-report.md`의 내부 인용 표기가 새 ChatGPT 프로젝트에서 연결되지 않을 경우를 대비한 공식 자료 목록입니다.

## 1. 데이터셋·CMP·Virtual Metrology

### PHM Society 2016 Data Challenge

- 설명: PHM 2016 CMP 데이터 챌린지 공식 페이지
- 확인 내용: 데이터 목적, MRR 예측 과제, 데이터 다운로드 안내
- URL: https://phmsociety.org/conference/annual-conference-of-the-phm-society/annual-conference-of-the-prognostics-and-health-management-society-2016/phm-data-challenge-4/

### Enhanced Virtual Metrology on Chemical Mechanical Polishing Processes

- 설명: PHM 2016 CMP 데이터를 활용한 Virtual Metrology 연구
- 확인 내용: CMP의 MRR 예측, pad·dresser 상태 변화, VM 활용 배경
- URL: https://papers.phmsociety.org/index.php/ijphm/article/download/2641/1598

### A Data-driven Approach to Material Removal Rate Prediction

- 설명: PHM 2016 CMP 데이터를 이용한 Feature Engineering과 Tree Ensemble 연구
- 확인 내용: 주요 변수, time-domain Feature, 모델 비교 방식
- URL: https://papers.phmsociety.org/index.php/phmconf/article/download/489/phmc_18_489

---

## 2. 검증 방법

### scikit-learn Cross-validation Guide

- 설명: Cross-validation과 TimeSeriesSplit 공식 문서
- 확인 내용: 시간 의존 데이터에서 무작위 분할의 문제, 시간순 검증 방법
- URL: https://scikit-learn.org/stable/modules/cross_validation.html

---

## 3. SPC

### NIST Process Control Techniques

- 설명: SPC와 공정 모니터링의 기본 개념
- 확인 내용: 관리한계, Phase I·Phase II, 공정 감시
- URL: https://www.itl.nist.gov/div898/handbook/pmc/section1/pmc12.htm

### NIST CUSUM Control Charts

- 설명: CUSUM 공식 설명
- URL: https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc323.htm

### NIST EWMA Control Charts

- 설명: EWMA 공식 설명
- URL: https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc324.htm

---

## 4. SHAP와 해석 주의사항

### A Unified Approach to Interpreting Model Predictions

- 설명: SHAP 원 논문
- 확인 내용: 개별 예측에 대한 Feature 기여도 설명
- URL: https://proceedings.neurips.cc/paper/7062-a-unified-approach-to-interpreting-model-predictions.pdf

### Quantifying the Limits of the Shapley Value for Explanations

- 설명: Shapley 기반 설명의 한계
- 확인 내용: 상관 Feature와 상호작용이 있을 때 과도한 인과 해석 금지
- URL: https://proceedings.neurips.cc/paper/2021/file/dfc6aa246e88ab3e32caeaaecf433550-Paper.pdf

---

## 5. SK하이닉스 직무 연결

### SK하이닉스 직무 소개

- URL: https://talent.skhynix.com/hub/ko/job/introduce

### DMI 소개

- URL: https://talent.skhynix.com/hub/ko/company/story/180

### 기반기술 소개

- URL: https://talent.skhynix.com/hub/ko/company/story/137

### PE 직무 인터뷰

- URL: https://talent.skhynix.com/hub/ko/job/interview/7

### 양산기술 직무 인터뷰

- URL: https://talent.skhynix.com/hub/en/job/interview/9

---

## 사용 원칙

- 기술적 결정은 블로그보다 공식 데이터셋 설명, 공식 문서, 원 논문을 우선합니다.
- 라이브러리 구현은 사용 중인 버전의 공식 Documentation을 다시 확인합니다.
- 채용 직무 설명은 지원 시점의 최신 공고와 Talent Hub를 다시 확인합니다.
- 참고 논문의 성능 수치를 프로젝트의 예상 성능이나 목표치로 그대로 사용하지 않습니다.
