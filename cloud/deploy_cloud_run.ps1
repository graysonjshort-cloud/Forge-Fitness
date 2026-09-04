param(
  [Parameter(Mandatory=$true)][string]$ProjectId,
  [string]$Region = "us-east1",
  [string]$Service = "forge-api"
)
$ErrorActionPreference = "Stop"
gcloud config set project $ProjectId
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
gcloud run deploy $Service `
  --source backend `
  --region $Region `
  --allow-unauthenticated `
  --port 8080 `
  --max-instances 1 `
  --concurrency 40 `
  --timeout 300 `
  --set-env-vars "FORGE_SERVE_FRONTEND=0,FORGE_DB_PATH=/tmp/forge/fitness_app.sqlite,FORGE_ALLOWED_ORIGINS=https://localhost|capacitor://localhost|http://localhost,FORGE_PERSISTENCE_KEY=forge-production-v17" `
  --set-secrets "SUPABASE_DB_URL=FORGE_SUPABASE_DB_URL:latest"
$ApiUrl = gcloud run services describe $Service --region $Region --format="value(status.url)"
Write-Host "Forge API deployed: $ApiUrl"
Write-Host "Then run: node scripts/set-api-base.mjs $ApiUrl"
Write-Host "If AI Coach is enabled, add OPENAI_API_KEY from Secret Manager to this Cloud Run service."
