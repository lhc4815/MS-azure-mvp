# AIPM PR Monitor — 5분 데모 시나리오

## 데모 목표
Azure 위에서 동작하는 AI 기반 PR 모니터링 에이전트의 **전체 파이프라인**을 라이브로 보여준다.

---

## 시나리오 흐름 (5분)

### [0:00 ~ 0:30] 인트로 — 문제 정의
> "기업 PR/홍보 담당자는 매일 수백 개의 뉴스를 수동으로 모니터링합니다.
> 이 에이전트는 뉴스 수집 → AI 분석 → 리포트 생성을 자동화합니다."

### [0:30 ~ 1:30] Azure 아키텍처 설명
**화면: Azure Portal 대시보드**

> "모든 리소스가 Azure 위에서 동작합니다."

보여줄 것:
- 리소스 그룹 `rg-aipm-mvp` — 전체 리소스 목록
- Azure Functions — 서버리스 실행 (Consumption Plan, 과금 최소화)
- Azure OpenAI — GPT-4o 모델로 뉴스 분석
- Cosmos DB — 분석 결과 저장 (Free Tier)

### [1:30 ~ 2:00] 코드 구조 간단 설명
**화면: GitHub 저장소 (https://github.com/lhc4815/MS-azure-mvp)**

> "Python Azure Functions v2로 개발했고, 인프라도 CLI 스크립트로 재현 가능합니다."

보여줄 것:
- `function_app.py` — 3개 엔드포인트 (스케줄/수동/조회)
- `infra/setup.sh` — Azure CLI 프로비저닝 스크립트
- README.md 아키텍처 다이어그램

### [2:00 ~ 3:30] 라이브 실행 ⚡
**화면: 터미널 또는 Postman**

```bash
# 삼성전자 키워드로 수동 실행
curl -X POST https://func-aipm-mvp.azurewebsites.net/api/monitor \
  -H "Content-Type: application/json" \
  -H "x-functions-key: <FUNCTION_KEY>" \
  -d '{"keywords": ["삼성전자", "SK하이닉스"]}'
```

> "실시간으로 Naver 뉴스를 수집하고, Azure OpenAI가 분석합니다."

보여줄 것:
- API 호출 → 약 6~8초 후 JSON 응답
- 응답 안에: 기사 수, 감성 분석 점수, 핵심 포인트, 위기 신호

### [3:30 ~ 4:15] 결과 확인
**화면: Azure Portal → Cosmos DB Data Explorer**

```bash
# 저장된 결과 조회
curl https://func-aipm-mvp.azurewebsites.net/api/results?limit=3 \
  -H "x-functions-key: <FUNCTION_KEY>"
```

> "분석 결과는 Cosmos DB에 자동 저장되어 이력 조회가 가능합니다."

보여줄 것:
- Data Explorer에서 방금 저장된 문서 클릭
- JSON 구조: summary, key_points, sentiment_analysis

### [4:15 ~ 4:45] 자동화 설명
> "Timer Trigger가 6시간마다 자동 실행합니다.
> Teams Webhook을 연결하면 분석 결과가 Adaptive Card로 채널에 전송됩니다."

보여줄 것:
- `function_app.py`의 Timer Trigger 코드 (cron: `0 0 */6 * * *`)
- Teams Adaptive Card 예시 (teams_notify.py 코드)

### [4:45 ~ 5:00] 클로징
> "Azure Functions + OpenAI + Cosmos DB를 조합해서
> 서버 관리 없이, 월 수천 원 수준으로 운영 가능한 AI 에이전트를 만들었습니다.
> 감사합니다."

---

## 데모 전 체크리스트

- [ ] Azure Portal 로그인 상태 확인
- [ ] Functions App 실행 가능 상태 확인 (`func-aipm-mvp`)
- [ ] Function Key 준비 (Portal → func-aipm-mvp → 앱 키)
- [ ] GitHub 저장소 공개 확인
- [ ] 터미널에 curl 명령어 미리 준비
- [ ] Cosmos DB Data Explorer 탭 미리 열어두기
- [ ] (선택) Teams Webhook URL 설정 완료
