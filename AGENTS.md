# FabLens 작업 지침

이 저장소에서 작업하기 전에 아래 기준 문서를 먼저 읽습니다.

## 필수 문서

1. `docs/project/01_PROJECT_SOURCE_OF_TRUTH.md`
2. `docs/project/02_AI_DEVELOPMENT_RULES.md`
3. `docs/project/03_TEAM_ROLES_AND_WBS.md`
4. `docs/project/04_TECHNICAL_DECISIONS.md`

추가 배경이 필요하면 다음 문서를 확인합니다.

- `docs/research/FabLens_FINAL_PROJECT_PLAN.md`
- `docs/references/01_REFERENCE_LINKS.md`

문서가 충돌하면 `PROJECT_SOURCE_OF_TRUTH`, `TECHNICAL_DECISIONS`,
`AI_DEVELOPMENT_RULES`, `TEAM_ROLES_AND_WBS`, `FINAL_PROJECT_PLAN` 순으로 따릅니다.

## 작업 원칙

- `data/raw/`의 원본 데이터는 수정, 삭제, 이동하거나 이름을 바꾸지 않습니다.
- 분석 단위, 데이터 분할, SPC 정책 등 확정된 기술 기준을 임의로 바꾸지 않습니다.
- 구현하지 않은 기능을 완료된 것처럼 표현하지 않습니다.
- 실제 Fab 적용, 수율 개선, 비용 절감 효과를 주장하지 않습니다.
- 사용자가 요청하지 않은 다음 단계까지 임의로 구현하지 않습니다.
- 중요한 기술 결정을 바꿔야 하면 먼저 사용자에게 알리고 결정 로그를 남깁니다.
- Git 명령은 사용자가 명시적으로 요청한 경우에만 실행합니다.
- 작업을 마치면 변경 파일, 검증 결과, 수행하지 않은 작업을 정확히 보고합니다.

