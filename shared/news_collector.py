"""News Collector — 네이버 뉴스 API 수집 + 중복 제거

insightforge의 NewsIntelligence를 Azure용으로 경량화.
"""
from __future__ import annotations

import os
import re
import hashlib
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger("aipm.collector")


async def collect_news(
    keywords: list[str],
    sources: list[str] | None = None,
    max_per_keyword: int = 20,
) -> dict:
    """키워드 기반 뉴스 수집 + 중복 제거 + 위기 신호 감지"""
    sources = sources or ["naver"]
    all_articles: list[dict] = []

    for keyword in keywords:
        if "naver" in sources:
            articles = await _fetch_naver_news(keyword, max_per_keyword)
            all_articles.extend(articles)

    deduplicated = _deduplicate(all_articles)

    # 위기 신호: 키워드당 50건 이상이면 급증
    crisis_signals = []
    for kw in keywords:
        count = sum(1 for a in deduplicated if kw in a.get("title", ""))
        if count >= 50:
            crisis_signals.append({
                "entity": kw,
                "article_count": count,
                "signal": "HIGH",
            })

    return {
        "articles": deduplicated,
        "article_count": len(deduplicated),
        "keywords": keywords,
        "crisis_signals": crisis_signals,
        "collected_at": datetime.utcnow().isoformat(),
    }


async def _fetch_naver_news(query: str, display: int = 20) -> list[dict]:
    """Naver Search API 호출"""
    client_id = os.getenv("NAVER_CLIENT_ID", "")
    client_secret = os.getenv("NAVER_CLIENT_SECRET", "")

    if not client_id:
        logger.warning("NAVER_CLIENT_ID 미설정 — mock 데이터 반환")
        return _mock_articles(query)

    url = "https://openapi.naver.com/v1/search/news.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {"query": query, "display": min(display, 100), "sort": "date"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, params=params) as resp:
                if resp.status != 200:
                    logger.error(f"Naver API error: {resp.status}")
                    return _mock_articles(query)

                data = await resp.json()
                return [
                    {
                        "title": _strip_html(item.get("title", "")),
                        "description": _strip_html(item.get("description", "")),
                        "link": item.get("originallink", item.get("link", "")),
                        "pub_date": item.get("pubDate", ""),
                        "source": "naver",
                        "content_hash": hashlib.md5(
                            f"{item.get('title','')}{item.get('link','')}".encode()
                        ).hexdigest(),
                    }
                    for item in data.get("items", [])
                ]
    except Exception as e:
        logger.error(f"Naver fetch error: {e}")
        return _mock_articles(query)


def _deduplicate(articles: list[dict]) -> list[dict]:
    seen: set[str] = set()
    result: list[dict] = []
    for a in articles:
        h = a.get("content_hash") or hashlib.md5(
            f"{a['title']}{a.get('link','')}".encode()
        ).hexdigest()
        if h not in seen:
            seen.add(h)
            result.append(a)
    return result


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def _mock_articles(query: str) -> list[dict]:
    now = datetime.utcnow()
    mocks = [
        f"{query}, 2026년 1분기 실적 시장 예상 상회",
        f"{query}, AI 반도체 신규 투자 발표",
        f"{query}, 美 수출규제 완화로 수혜 전망",
        f"증권가, {query} 목표주가 상향 조정",
        f"{query}, 글로벌 공급망 재편 수혜 기대",
    ]
    return [
        {
            "title": title,
            "description": f"{title} — 상세 내용",
            "link": f"https://example.com/news/{i}",
            "pub_date": now.strftime("%a, %d %b %Y %H:%M:%S +0900"),
            "source": "mock",
            "content_hash": hashlib.md5(title.encode()).hexdigest(),
        }
        for i, title in enumerate(mocks, 1)
    ]
