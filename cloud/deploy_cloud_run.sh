#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-${1:-}}"
REGION="${FORGE_CLOUD_REGION:-${2:-us-east1}}"
SERVICE="${FORGE_CLOUD_SERVICE:-forge-api}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Usage: GOOGLE_CLOUD_PROJECT=your-project ./cloud/deploy_cloud_run.sh"
  exit 2
fi

gcloud config set project "$PROJECT_ID" >/dev/null
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com

ARGS=(
  run deploy "$SERVICE"
  --source backend
  --region "$REGION"
  --allow-unauthenticated
  --port 8080
  --max-instances 1
  --concurrency 40
  --timeout 300
  --set-env-vars "FORGE_SERVE_FRONTEND=0,FORGE_DB_PATH=/tmp/forge/fitness_app.sqlite,FORGE_ALLOWED_ORIGINS=https://localhost|capacitor://localhost|http://localhost,FORGE_PERSISTENCE_KEY=${FORGE_PERSISTENCE_KEY:-forge-production-v17}"
  --set-secrets "SUPABASE_DB_URL=FORGE_SUPABASE_DB_URL:latest"
)

if [[ "${FORGE_USE_OPENAI_SECRET:-0}" == "1" ]]; then
  ARGS+=(--set-secrets "OPENAI_API_KEY=FORGE_OPENAI_API_KEY:latest")
fi

gcloud "${ARGS[@]}"

URL="$(gcloud run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo "Forge API deployed: $URL"
echo "Configure Android with:"
echo "  node scripts/set-api-base.mjs $URL"
