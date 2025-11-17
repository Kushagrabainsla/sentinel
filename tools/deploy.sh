#!/usr/bin/env bash
set -euo pipefail
REGION="${1:-us-east-1}"

python3 -m pip install -r services/events_api/requirements.txt -t services/events_api || true
python3 -m pip install -r services/tracker_builder/requirements.txt -t services/tracker_builder || true

pushd infra >/dev/null
terraform init -upgrade
terraform fmt -recursive
terraform validate
terraform plan -out tfplan -var="stage=prod" -var="region=${REGION}"
terraform apply -auto-approve tfplan
terraform output
popd >/dev/null
