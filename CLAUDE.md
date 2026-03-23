# MS Azure MVP — PR 모니터링 에이전트

## Project Overview
- **기간:** 2026.03.17 ~ 03.28 (2주)
- **목표:** Azure 위에서 동작하는 PR 모니터링 에이전트 MVP 완성 + 5분 데모
- **기존 코드:** ~/Projects/insightforge (로컬 프로토타입)
- **로컬 프로젝트:** ~/Projects/MS-azure-mvp

## Azure Stack
- Azure Functions (Timer Trigger 6h + HTTP Trigger)
- Azure OpenAI Service (GPT-4o, eastus)
- Azure Cosmos DB (NoSQL, Free Tier)
- Teams Incoming Webhook (Adaptive Card 알림)
- Naver Search API (한국 뉴스 수집)

## 현재 진행 상태 (Day 3, 2026-03-19)
### 완료
- [x] Azure CLI 로그인 + 리소스 그룹 생성
- [x] Azure OpenAI GPT-4o 모델 배포 (GlobalStandard, eastus)
- [x] Cosmos DB 프로비저닝 (DB: aipm / Container: pr_monitor)
- [x] Azure Functions 로컬 테스트 성공
- [x] Azure Functions 배포 (func-aipm-mvp) + 라이브 테스트 성공
- [x] GPT-4o 실제 AI 분석 파이프라인 동작 확인 (6.5초, 감성분석 0.9)
- [x] Naver API 연동 완료 — 실제 뉴스 수집 (38건, 2키워드, 8.1초)
- [x] 전체 파이프라인 엔드투엔드 라이브 테스트 성공

### 남은 작업
- [ ] Teams Webhook 연동 (코드 완성됨, URL만 필요)
- [ ] 파이프라인 안정화 (에러 핸들링, 로깅)
- [ ] 5분 데모 시나리오 준비 (2주차)
- [ ] 현대차 교육 제안서 (마감 3/23)

## 파이프라인 구조
```
Timer/HTTP Trigger → News Collector (Naver API) → Azure OpenAI Analyzer (GPT-4o)
→ Result Builder → Cosmos DB 저장 + Teams 알림
```

## 코드 구조
```
function_app.py          # Azure Functions 엔트리포인트 (3개 엔드포인트)
shared/
  __init__.py
  news_collector.py      # Naver API 뉴스 수집 + 중복제거 + 위기신호
  analyzer.py            # Azure OpenAI GPT-4o 분석
  pipeline.py            # 수집→분석→결과 파이프라인
  cosmos_client.py       # Cosmos DB 저장/조회
  teams_notify.py        # Teams Adaptive Card 알림
```

## Build & Run
- Python 3.11+
- `pip install -r requirements.txt`
- 로컬: `func start`
- 배포: `func azure functionapp publish func-aipm-mvp`

## Code Style
- Python PEP 8, type hints
- Azure Functions v2 프로그래밍 모델
- 한국어 주석 OK, 코드/변수명은 영문
- 모든 모듈에 graceful fallback (API 미설정 시 mock 반환)

## Azure Resources
- **Subscription**: Azure subscription 1 (4bdfab1a-1a45-4994-b856-44ab77db6350)
- **Resource Group**: rg-aipm-mvp (koreacentral)
- **Azure OpenAI**: aoai-aipm-mvp-eastus (eastus) — GPT-4o 배포 완료
- **Cosmos DB**: cosmos-aipm-mvp (koreacentral, Free Tier)
  - Database: aipm / Container: pr_monitor
- **Functions App**: func-aipm-mvp (koreacentral, Consumption Plan)
- **Storage**: staipmvp (koreacentral)

## Notion 작업 로그
- **MVP 작업 로그**: https://www.notion.so/32652a8fb96e81c19b71c77ffeff0ca7
- **기록 방침**: 내부 매뉴얼로 재활용 가능하도록 CLI 명령어, 에러→해결, Azure 공식문서 링크 포함
- **스크린샷**: imgbb API로 업로드 후 Notion 임베드
