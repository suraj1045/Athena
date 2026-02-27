#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Athena — Deploy SageMaker model artifact to S3
#
# Usage: ./scripts/deploy_model.sh <model_type> <model_path>
# Example: ./scripts/deploy_model.sh yolo src/ml_models/yolo_detector/weights/best.pt
#
# Packages the model into a tar.gz and uploads to S3
# ─────────────────────────────────────────────────────────────

set -euo pipefail

MODEL_TYPE="${1:?Usage: deploy_model.sh <yolo|anpr> <model_path>}"
MODEL_PATH="${2:?Please provide the path to the model weights}"
ENVIRONMENT="${ATHENA_ENVIRONMENT:-dev}"
S3_BUCKET="athena-models-${ENVIRONMENT}"

echo "🚀 Deploying ${MODEL_TYPE} model to s3://${S3_BUCKET}/${MODEL_TYPE}/"

# Package model artifact
TMPDIR=$(mktemp -d)
cp "${MODEL_PATH}" "${TMPDIR}/model.onnx" 2>/dev/null || cp "${MODEL_PATH}" "${TMPDIR}/model.pt"

# Copy inference script
if [ "${MODEL_TYPE}" = "yolo" ]; then
    cp src/ml_models/sagemaker/inference_yolo.py "${TMPDIR}/inference.py"
elif [ "${MODEL_TYPE}" = "anpr" ]; then
    cp src/ml_models/sagemaker/inference_anpr.py "${TMPDIR}/inference.py"
fi

cd "${TMPDIR}"
tar -czf model.tar.gz .
aws s3 cp model.tar.gz "s3://${S3_BUCKET}/${MODEL_TYPE}/model.tar.gz"
cd -

echo "✅ Model deployed: s3://${S3_BUCKET}/${MODEL_TYPE}/model.tar.gz"
rm -rf "${TMPDIR}"
