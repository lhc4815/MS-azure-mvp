"""Pipeline — 수집 → 분석 → 결과 반환

Azure Functions에서 호출하는 메인 파이프라인.
"""
from __future__ import annotations

import logging
from datetime import datetime
from uuid import uuid4

from shared.news_collector import collect_news
from shared.analyzer import analyze_articles

logger = logging.getLogger("aipm.pipeline")


async def run_pipeline(
    keywords: list[str],
    sources: list[str] | None = None,
    user_context: str = "",
) -> dict:
    """PR 모니터링 파이프라인 1회 실행

    Returns:
        실행 결과 dict (Cosmos DB 저장용)
    """
    execution_id = str(uuid4())[:8]
    started_at = datetime.utcnow()

    logger.info(f"Pipeline 시작 [{execution_id}]: keywords={keywords}")

    # Step 1: 뉴스 수집
    collected = await collect_news(
        keywords=keywords,
        sources=sources or ["naver"],
    )
    logger.info(f"수집 완료: {collected['article_count']}건")

    # Step 2: AI 분석
    analysis = await analyze_articles(
        collected_data=collected,
        user_context=user_context,
    )
    logger.info(f"분석 완료: 핵심포인트 {len(analysis.get('key_points', []))}개")

    # 결과 조합
    finished_at = datetime.utcnow()
    duration_sec = (finished_at - started_at).total_seconds()

    return {
        "id": execution_id,
        "keywords": keywords,
        "article_count": collected["article_count"],
        "crisis_signals": collected.get("crisis_signals", []),
        "summary": analysis.get("summary", ""),
        "key_points": analysis.get("key_points", []),
        "sentiment_analysis": analysis.get("sentiment_analysis", {}),
        "mentioned_entities": analysis.get("mentioned_entities", []),
        "full_report": analysis.get("full_report", ""),
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_sec": round(duration_sec, 1),
    }
