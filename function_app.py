"""AIPM PR Monitor — Azure Functions Entry Point

Timer Trigger: 6시간마다 자동 실행
HTTP Trigger: 수동 실행 및 결과 조회
"""
import azure.functions as func
import json
import logging

from shared.pipeline import run_pipeline
from shared.cosmos_client import CosmosStore
from shared.teams_notify import send_teams_notification

app = func.FunctionApp()
logger = logging.getLogger("aipm")


# ─── Timer Trigger: 6시간마다 자동 실행 ─────────────────────
@app.timer_trigger(
    schedule="0 0 */6 * * *",  # 매 6시간
    arg_name="timer",
    run_on_startup=False,
)
async def pr_monitor_scheduled(timer: func.TimerRequest) -> None:
    """스케줄 기반 PR 모니터링 실행"""
    logger.info("PR Monitor 스케줄 실행 시작")

    result = await run_pipeline(
        keywords=["삼성전자", "SK하이닉스", "현대자동차"],
        sources=["naver"],
    )

    # Cosmos DB 저장
    store = CosmosStore()
    await store.save_execution(result)

    # Teams 알림
    await send_teams_notification(result)

    logger.info(f"PR Monitor 완료: {result['article_count']}건 분석")


# ─── HTTP Trigger: 수동 실행 ────────────────────────────────
@app.route(route="monitor", methods=["POST"], auth_level=func.AuthLevel.FUNCTION)
async def pr_monitor_manual(req: func.HttpRequest) -> func.HttpResponse:
    """수동 실행 — POST /api/monitor {"keywords": ["삼성전자"]}"""
    logger.info("PR Monitor 수동 실행")

    try:
        body = req.get_json()
    except ValueError:
        body = {}

    keywords = body.get("keywords", ["삼성전자", "SK하이닉스"])
    sources = body.get("sources", ["naver"])

    result = await run_pipeline(keywords=keywords, sources=sources)

    # Cosmos DB 저장
    store = CosmosStore()
    await store.save_execution(result)

    # Teams 알림
    await send_teams_notification(result)

    return func.HttpResponse(
        json.dumps(result, ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=200,
    )


# ─── HTTP Trigger: 최근 결과 조회 ──────────────────────────
@app.route(route="results", methods=["GET"], auth_level=func.AuthLevel.FUNCTION)
async def get_results(req: func.HttpRequest) -> func.HttpResponse:
    """최근 실행 결과 조회 — GET /api/results?limit=5"""
    limit = int(req.params.get("limit", "5"))

    store = CosmosStore()
    results = await store.get_recent_executions(limit=limit)

    return func.HttpResponse(
        json.dumps(results, ensure_ascii=False, indent=2),
        mimetype="application/json",
        status_code=200,
    )
