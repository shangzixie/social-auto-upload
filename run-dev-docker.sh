#!/usr/bin/env sh
set -eu

docker rm -f social-auto-upload-dev >/dev/null 2>&1 || true

mkdir -p db videoFile cookiesFile

docker run -d -it \
  --name social-auto-upload-dev \
  -p 5409:5409 \
  -v "$(pwd)/sau_backend.py:/app/sau_backend.py" \
  -v "$(pwd)/myUtils:/app/myUtils" \
  -v "$(pwd)/uploader:/app/uploader" \
  -v "$(pwd)/utils:/app/utils" \
  -v "$(pwd)/sau_backend:/app/sau_backend" \
  -v "$(pwd)/db:/app/db" \
  -v "$(pwd)/videoFile:/app/videoFile" \
  -v "$(pwd)/cookiesFile:/app/cookiesFile" \
  social-auto-upload:latest \
  sh -lc "python /app/db/createTable.py && python sau_backend.py"

echo "Dev container started: social-auto-upload-dev"
echo "Open: http://localhost:5409"
