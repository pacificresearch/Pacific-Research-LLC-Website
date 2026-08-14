#!/usr/bin/env bash
# Deploy site/ to Netlify (pacificresearchllc.com).
# Requires NETLIFY_AUTH_TOKEN env var (set in the cloud environment's
# variables — never commit the token).
set -euo pipefail
SITE_ID="96d0bf1a-e9f1-4483-a2b0-cbeceec73b19"
cd "$(dirname "$0")/../site"
rm -f /tmp/deploy.zip
zip -qr /tmp/deploy.zip . -x ".*"
resp=$(curl -sS -m 180 -X POST \
  "https://api.netlify.com/api/v1/sites/${SITE_ID}/deploys" \
  -H "Authorization: Bearer ${NETLIFY_AUTH_TOKEN}" \
  -H "Content-Type: application/zip" \
  --data-binary "@/tmp/deploy.zip")
id=$(echo "$resp" | python3 -c "import json,sys;print(json.load(sys.stdin)['id'])")
echo "deploy id: $id"
for i in $(seq 1 24); do
  state=$(curl -sS -m 20 "https://api.netlify.com/api/v1/sites/${SITE_ID}/deploys/${id}" \
    -H "Authorization: Bearer ${NETLIFY_AUTH_TOKEN}" \
    | python3 -c "import json,sys;print(json.load(sys.stdin)['state'])")
  echo "state: $state"
  [ "$state" = "ready" ] && exit 0
  [ "$state" = "error" ] && exit 1
  sleep 5
done
exit 1
