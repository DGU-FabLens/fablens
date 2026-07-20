# FabLens 데이터 디렉터리

- `raw/`: 수정하지 않는 원본 데이터
- `interim/`: 원본에서 생성한 중간 가공 결과
- `processed/`: 모델 입력용 최종 데이터

현재 PHM 2016 CMP 원본은 `raw/phm2016_cmp/`에 있습니다. training 시계열 CSV,
`CMP-training-removalrate.csv`, `LICENSE.txt`, `SOURCE_README.md`를 포함합니다.

`training/CMP-training-066.csv`는 알려진 헤더 전용 빈 파일입니다. 원본 보존을 위해
삭제하지 않습니다. 생성 데이터는 이후 코드로 재생성하며 일반적으로 Git에 포함하지
않습니다. 원본 데이터 검증과 profiling은 다음 개발 단계에서 구현할 예정입니다.

