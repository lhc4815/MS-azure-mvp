"""Analyzer — Azure OpenAI GPT-4o 기반 분석

insightforge AnalystAgent를 Azure OpenAI용으로 전환.
"""
from __future__ import annotations

import os
import json
import logging
from datetime import datetime

from openai import AsyncAzureOpenAI

logger = logging.getLogger("aipm.analyzer")


async def analyze_articles(
    collected_data: dict,
    user_context: str = "",
) -> dict:
    """수집된 뉴스를 분석하여 구조화된 결과 반환"""
    articles = collected_data.get("articles", [])
    keywords = collected_data.get("keywords", [])
    crisis_signals = collected_data.get("crisis_signals", [])

    if not articles:
        return _empty_result()

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")

    if not endpoint or not api_key:
        logger.warning("Azure OpenAI 미설정 — mock 분석 반환")
        return _mock_analysis(articles, keywords)

    client = AsyncAzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version="2024-08-01-preview",
    )

    prompt = _build_prompt(articles, keywords, crisis_signals, user_context)

    try:
        response = await client.chat.completions.create(
            model=deployment,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "당신은 기업 미디어 인텔리전스 분석가입니다. "
                        "뉴스 데이터를 분석하여 구조화된 보고서를 JSON으로 작성합니다. "
                        "반드시 JSON 형식만 반환하세요."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=4096,
            temperature=0.3,
        )
        text = response.choices[0].message.content or ""
        return _parse_json(text)

    except Exception as e:
        logger.error(f"Azure OpenAI 호출 에러: {e}")
        return _mock_analysis(articles, keywords)


def _build_prompt(
    articles: list[dict],
    keywords: list[str],
    crisis_signals: list[dict],
    user_context: str,
) -> str:
    articles_text = ""
    for i, a in enumerate(articles[:20], 1):
        articles_text += (
            f"\n[기사 {i}]\n제목: {a['title']}\n"
            f"내용: {a.get('description', '')}\n"
            f"출처: {a.get('link', '')}\n"
            f"날짜: {a.get('pub_date', '')}\n"
        )

    crisis_text = ""
    if crisis_signals:
        crisis_text = "\n⚠️ 위기 신호 감지:\n" + "\n".join(
            f"- {s['entity']}: {s['article_count']}건" for s in crisis_signals
        )

    context_text = f"\n[사용자 선호]\n{user_context}" if user_context else ""

    return f"""다음 뉴스 기사들을 분석하여 JSON으로 보고서를 작성하세요.

모니터링 키워드: {', '.join(keywords)}
{crisis_text}{context_text}

수집된 기사 ({len(articles)}건):
{articles_text}

반드시 아래 JSON 형식만 반환:
{{
    "summary": "전체 요약 (2-3문단)",
    "key_points": ["핵심 포인트 1 (출처 포함)", "..."],
    "sentiment_analysis": {{
        "키워드": {{"score": 0.0~1.0, "reasoning": "근거"}}
    }},
    "mentioned_entities": ["주요 기업/인물/기관"],
    "full_report": "마크다운 분석 보고서"
}}"""


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass
    return {
        "summary": text[:500],
        "key_points": [],
        "sentiment_analysis": {},
        "mentioned_entities": [],
        "full_report": text,
    }


def _empty_result() -> dict:
    return {
        "summary": "수집된 기사가 없습니다.",
        "key_points": [],
        "sentiment_analysis": {},
        "mentioned_entities": [],
        "full_report": "",
    }


def _mock_analysis(articles: list[dict], keywords: list[str]) -> dict:
    return {
        "summary": (
            f"[{', '.join(keywords)}] 관련 {len(articles)}건 분석. "
            f"전반적으로 긍정 기조. AI 투자 확대와 실적 호조가 주요 뉴스."
        ),
        "key_points": [
            f"{keywords[0]} 1분기 실적 시장 예상 상회",
            "AI 반도체 신규 투자 발표",
            "글로벌 수출규제 완화 수혜 전망",
        ],
        "sentiment_analysis": {
            kw: {"score": 0.72, "reasoning": "투자 확대 및 실적 호조 보도 우세"}
            for kw in keywords
        },
        "mentioned_entities": keywords + ["AI", "반도체", "미국 상무부"],
        "full_report": (
            f"# PR 모니터링 보고서\n\n"
            f"**키워드**: {', '.join(keywords)}\n"
            f"**기사 수**: {len(articles)}건\n"
            f"**시각**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            f"## 요약\n전반적으로 긍정적 보도 기조.\n"
        ),
    }
