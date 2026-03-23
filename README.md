# AIPM PR Monitor — Azure MVP

기업 미디어 인텔리전스를 자동화하는 서버리스 PR 모니터링 에이전트.
Azure Functions 위에서 뉴스를 수집하고, AI로 분석하고, Teams로 알림을 보냅니다.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Azure Functions (func-aipm-mvp)          │
│                                                             │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │ Timer Trigger │   │ HTTP Trigger │   │ HTTP Trigger   │  │
│  │ (6시간 주기)  │   │ POST /monitor│   │ GET /results   │  │
│  └──────┬───────┘   └──────┬───────┘   └───────┬────────┘  │
│         │                  │                    │           │
│         ▼                  ▼                    │           │
│  ┌─────────────────────────────┐                │           │
│  │        Pipeline             │                │           │
│  │  ┌─────────┐  ┌──────────┐ │                │           │
│  │  │  Naver   │→│  Azure   │ │                │           │
│  │  │  Search  │  │ OpenAI   │ │                │           │
│  │  │  API     │  │ GPT-4o   │ │                │           │
│  │  └─────────┘  └──────────┘ │                │           │
│  └──────────┬─────────────────┘                │           │
│             │                                   │           │
│             ▼                                   ▼           │
│  ┌──────────────────┐              ┌───────────────────┐   │
│  │   Cosmos DB      │◄─────────── │   결과 조회        │   │
│  │   (분석 결과 저장)│              └───────────────────┘   │
│  └──────────────────┘                                      │
│             │                                               │
│             ▼                                               │
│  ┌──────────────────┐                                      │
│  │  Teams Webhook    │                                      │
│  │  (Adaptive Card)  │                                      │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

## Azure 리소스

| 리소스 | 이름 | 리전 | 용도 |
|--------|------|------|------|
| Resource Group | `rg-aipm-mvp` | koreacentral | 전체 리소스 관리 |
| Azure OpenAI | `aoai-aipm-mvp-eastus` | eastus | GPT-4o 뉴스 분석 |
| Cosmos DB | `cosmos-aipm-mvp` | koreacentral | 분석 결과 저장 (Free Tier) |
| Functions App | `func-aipm-mvp` | koreacentral | 서버리스 실행 (Consumption) |
| Storage | `staipmvp` | koreacentral | Functions 런타임 스토리지 |

## 프로젝트 구조

```
MS-azure-mvp/
├── function_app.py          # Azure Functions 엔트리포인트 (3개 엔드포인트)
├── shared/
│   ├── news_collector.py    # Naver Search API 뉴스 수집 + 중복제거
│   ├── analyzer.py          # Azure OpenAI GPT-4o 분석
│   ├── pipeline.py          # 수집 → 분석 → 결과 파이프라인
│   ├── cosmos_client.py     # Cosmos DB 저장/조회
│   └── teams_notify.py      # Teams Adaptive Card 알림
├── infra/
│   └── setup.sh             # Azure CLI 인프라 프로비저닝 스크립트
├── host.json                # Azure Functions 호스트 설정
├── requirements.txt         # Python 의존성
└── README.md
```

## Quick Start

### 사전 요구사항
- Python 3.11+
- [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local) v4
- [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli)

### 로컬 실행
```bash
pip install -r requirements.txt
func start
```

### Azure 배포
```bash
# 인프라가 없으면 먼저 프로비저닝
chmod +x infra/setup.sh
./infra/setup.sh

# 함수 앱 배포
func azure functionapp publish func-aipm-mvp
```

### API 테스트
```bash
# 수동 실행
curl -X POST https://func-aipm-mvp.azurewebsites.net/api/monitor \
  -H "Content-Type: application/json" \
  -d '{"keywords": ["삼성전자"]}'

# 결과 조회
curl https://func-aipm-mvp.azurewebsites.net/api/results?limit=5
```

## 파이프라인 흐름

1. **뉴스 수집** — Naver Search API로 키워드별 최신 뉴스 수집, MD5 해시 기반 중복 제거
2. **AI 분석** — Azure OpenAI GPT-4o가 수집된 기사를 분석하여 요약, 감성분석, 핵심 포인트 추출
3. **결과 저장** — Cosmos DB에 JSON 형태로 저장, 이력 조회 가능
4. **알림 전송** — Teams Incoming Webhook으로 Adaptive Card 형태의 리포트 전송
