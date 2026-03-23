#!/bin/bash
# ============================================================
# AIPM PR Monitor — Azure 인프라 프로비저닝 스크립트
# 이 스크립트는 프로젝트에 사용된 Azure CLI 명령어를 재현 가능하도록 정리한 것입니다.
# 실행 전 az login 필요
# ============================================================

set -e

# ── 변수 ──────────────────────────────────────────────────
SUBSCRIPTION="4bdfab1a-1a45-4994-b856-44ab77db6350"
RESOURCE_GROUP="rg-aipm-mvp"
LOCATION="koreacentral"
OPENAI_LOCATION="eastus"

OPENAI_NAME="aoai-aipm-mvp-eastus"
COSMOS_NAME="cosmos-aipm-mvp"
FUNCTIONS_NAME="func-aipm-mvp"
STORAGE_NAME="staipmvp"

# ── 1. 로그인 & 구독 설정 ─────────────────────────────────
az account set --subscription "$SUBSCRIPTION"
echo "✅ 구독 설정 완료: $SUBSCRIPTION"

# ── 2. 리소스 그룹 생성 ───────────────────────────────────
az group create \
  --name "$RESOURCE_GROUP" \
  --location "$LOCATION"
echo "✅ 리소스 그룹 생성: $RESOURCE_GROUP ($LOCATION)"

# ── 3. Azure OpenAI 리소스 생성 + GPT-4o 배포 ─────────────
az cognitiveservices account create \
  --name "$OPENAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --kind OpenAI \
  --sku S0 \
  --location "$OPENAI_LOCATION"

az cognitiveservices account deployment create \
  --name "$OPENAI_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --deployment-name "gpt-4o" \
  --model-name "gpt-4o" \
  --model-version "2024-08-06" \
  --model-format OpenAI \
  --sku-capacity 10 \
  --sku-name "GlobalStandard"
echo "✅ Azure OpenAI + GPT-4o 배포 완료: $OPENAI_NAME ($OPENAI_LOCATION)"

# ── 4. Cosmos DB 생성 (Free Tier) ─────────────────────────
az cosmosdb create \
  --name "$COSMOS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --locations regionName="$LOCATION" \
  --enable-free-tier true

az cosmosdb sql database create \
  --account-name "$COSMOS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --name "aipm"

az cosmosdb sql container create \
  --account-name "$COSMOS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --database-name "aipm" \
  --name "pr_monitor" \
  --partition-key-path "/id"
echo "✅ Cosmos DB 생성: $COSMOS_NAME (DB: aipm / Container: pr_monitor)"

# ── 5. Storage Account 생성 ───────────────────────────────
az storage account create \
  --name "$STORAGE_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --sku Standard_LRS
echo "✅ Storage 생성: $STORAGE_NAME"

# ── 6. Azure Functions App 생성 ───────────────────────────
az functionapp create \
  --name "$FUNCTIONS_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --storage-account "$STORAGE_NAME" \
  --consumption-plan-location "$LOCATION" \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --os-type Linux
echo "✅ Functions App 생성: $FUNCTIONS_NAME"

# ── 7. Functions App에 환경변수 설정 ──────────────────────
# 아래 값들은 실제 배포 시 Azure Portal 또는 CLI에서 설정
# az functionapp config appsettings set \
#   --name "$FUNCTIONS_NAME" \
#   --resource-group "$RESOURCE_GROUP" \
#   --settings \
#     AZURE_OPENAI_ENDPOINT="<endpoint>" \
#     AZURE_OPENAI_API_KEY="<key>" \
#     AZURE_OPENAI_DEPLOYMENT="gpt-4o" \
#     COSMOS_DB_ENDPOINT="<endpoint>" \
#     COSMOS_DB_KEY="<key>" \
#     COSMOS_DB_DATABASE="aipm" \
#     COSMOS_DB_CONTAINER="pr_monitor" \
#     NAVER_CLIENT_ID="<id>" \
#     NAVER_CLIENT_SECRET="<secret>"

echo ""
echo "============================================================"
echo "🎉 인프라 프로비저닝 완료!"
echo ""
echo "다음 단계:"
echo "  1. func start              — 로컬 테스트"
echo "  2. func azure functionapp publish $FUNCTIONS_NAME — 배포"
echo "============================================================"
