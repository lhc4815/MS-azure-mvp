"""Teams Notification — Webhook을 통한 알림 전송

Adaptive Card 형태로 분석 결과를 Teams 채널에 전송.
"""
from __future__ import annotations

import os
import logging

import aiohttp

logger = logging.getLogger("aipm.teams")


async def send_teams_notification(result: dict) -> bool:
    """Teams Incoming Webhook으로 분석 결과 전송"""
    webhook_url = os.getenv("TEAMS_WEBHOOK_URL", "")

    if not webhook_url:
        logger.info("TEAMS_WEBHOOK_URL 미설정 — 알림 건너뜀")
        _print_local(result)
        return False

    card = _build_adaptive_card(result)

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                webhook_url,
                json=card,
                headers={"Content-Type": "application/json"},
            ) as resp:
                if resp.status == 200:
                    logger.info("Teams 알림 전송 완료")
                    return True
                else:
                    logger.error(f"Teams 알림 실패: {resp.status}")
                    return False
    except Exception as e:
        logger.error(f"Teams 알림 에러: {e}")
        return False


def _build_adaptive_card(result: dict) -> dict:
    """Adaptive Card 메시지 빌드"""
    keywords = ", ".join(result.get("keywords", []))
    summary = result.get("summary", "요약 없음")
    article_count = result.get("article_count", 0)
    key_points = result.get("key_points", [])
    crisis = result.get("crisis_signals", [])

    # 감성 분석 요약
    sentiment_text = ""
    for entity, data in result.get("sentiment_analysis", {}).items():
        if isinstance(data, dict):
            score = data.get("score", 0.5)
        else:
            score = float(data)
        label = "🟢 긍정" if score > 0.6 else "🔴 부정" if score < 0.4 else "🟡 중립"
        sentiment_text += f"- **{entity}**: {label} ({score:.2f})\n"

    # 위기 신호
    crisis_text = ""
    if crisis:
        crisis_text = "\n\n🚨 **위기 신호 감지**\n" + "\n".join(
            f"- {c['entity']}: {c['article_count']}건 급증" for c in crisis
        )

    # 핵심 포인트
    points_text = "\n".join(f"- {p}" for p in key_points[:5])

    return {
        "type": "message",
        "attachments": [
            {
                "contentType": "application/vnd.microsoft.card.adaptive",
                "content": {
                    "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                    "type": "AdaptiveCard",
                    "version": "1.4",
                    "body": [
                        {
                            "type": "TextBlock",
                            "text": f"📊 PR 모니터링 리포트",
                            "weight": "Bolder",
                            "size": "Large",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"키워드: {keywords} | 기사: {article_count}건",
                            "isSubtle": True,
                            "spacing": "None",
                        },
                        {
                            "type": "TextBlock",
                            "text": summary,
                            "wrap": True,
                            "spacing": "Medium",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**핵심 포인트**\n{points_text}",
                            "wrap": True,
                            "spacing": "Medium",
                        },
                        {
                            "type": "TextBlock",
                            "text": f"**감성 분석**\n{sentiment_text}{crisis_text}",
                            "wrap": True,
                            "spacing": "Medium",
                        },
                    ],
                },
            }
        ],
    }


def _print_local(result: dict) -> None:
    """로컬 개발 시 콘솔 출력"""
    print("\n" + "=" * 60)
    print("📊 PR Monitor 결과 (로컬)")
    print("=" * 60)
    print(f"키워드: {', '.join(result.get('keywords', []))}")
    print(f"기사 수: {result.get('article_count', 0)}")
    print(f"\n요약: {result.get('summary', '')}")
    for i, p in enumerate(result.get("key_points", []), 1):
        print(f"  {i}. {p}")
    print("=" * 60)
