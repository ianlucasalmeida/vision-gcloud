#!/bin/bash
PROJECT_ID="vision-gcloud"
FUNCTION_NAME="generate-upload-url"
REGION="southamerica-east1"
SERVICE_ACCOUNT="sa-url-generator@${PROJECT_ID}.iam.gserviceaccount.com"
UPLOAD_BUCKET="vision-gcloud-uploads"

echo ">>> Iniciando deploy da função '${FUNCTION_NAME}'..."
gcloud functions deploy ${FUNCTION_NAME} \
  --gen2 \
  --runtime=python311 \
  --project=${PROJECT_ID} \
  --region=${REGION} \
  --source=. \
  --entry-point=${FUNCTION_NAME} \
  --trigger-http \
  --allow-unauthenticated \
  --service-account=${SERVICE_ACCOUNT} \
  --set-env-vars="UPLOAD_BUCKET_NAME=${UPLOAD_BUCKET},SIGNING_SERVICE_ACCOUNT_EMAIL=${SERVICE_ACCOUNT}"
echo ">>> Deploy de '${FUNCTION_NAME}' concluído."