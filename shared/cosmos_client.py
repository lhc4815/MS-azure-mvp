"""Cosmos DB Client — 실행 결과 저장/조회

Azure Cosmos DB NoSQL API 사용.
Free Tier 범위 내 동작.
"""
from __future__ import annotations

import os
import logging
from datetime import datetime

logger = logging.getLogger("aipm.cosmos")

# Cosmos DB SDK는 Azure 배포 시 사용
# 로컬 개발 시에는 in-memory fallback
_local_store: list[dict] = []


class CosmosStore:
    """Cosmos DB 저장소 (로컬 fallback 포함)"""

    def __init__(self):
        self.endpoint = os.getenv("COSMOS_DB_ENDPOINT", "")
        self.key = os.getenv("COSMOS_DB_KEY", "")
        self.database_name = os.getenv("COSMOS_DB_DATABASE", "aipm")
        self.container_name = os.getenv("COSMOS_DB_CONTAINER", "pr_monitor")
        self._client = None
        self._container = None

    async def _get_container(self):
        if self._container:
            return self._container

        if not self.endpoint or not self.key:
            logger.info("Cosmos DB 미설정 — 로컬 메모리 사용")
            return None

        try:
            from azure.cosmos.aio import CosmosClient

            self._client = CosmosClient(self.endpoint, self.key)
            db = self._client.get_database_client(self.database_name)
            self._container = db.get_container_client(self.container_name)
            return self._container
        except Exception as e:
            logger.error(f"Cosmos DB 연결 실패: {e}")
            return None

    async def save_execution(self, result: dict) -> None:
        """실행 결과 저장"""
        container = await self._get_container()

        if container:
            try:
                await container.upsert_item(result)
                logger.info(f"Cosmos DB 저장 완료: {result['id']}")
            except Exception as e:
                logger.error(f"Cosmos DB 저장 실패: {e}")
                _local_store.append(result)
        else:
            _local_store.append(result)
            logger.info(f"로컬 저장: {result['id']} (총 {len(_local_store)}건)")

    async def get_recent_executions(self, limit: int = 5) -> list[dict]:
        """최근 실행 결과 조회"""
        container = await self._get_container()

        if container:
            try:
                query = (
                    "SELECT * FROM c ORDER BY c.started_at DESC OFFSET 0 LIMIT @limit"
                )
                items = []
                async for item in container.query_items(
                    query=query,
                    parameters=[{"name": "@limit", "value": limit}],
                ):
                    items.append(item)
                return items
            except Exception as e:
                logger.error(f"Cosmos DB 조회 실패: {e}")

        return sorted(
            _local_store,
            key=lambda x: x.get("started_at", ""),
            reverse=True,
        )[:limit]

    async def close(self):
        if self._client:
            await self._client.close()
