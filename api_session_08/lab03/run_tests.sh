#!/usr/bin/env bash
# Lab 3 - Chay Newman doc lap, khong can Postman UI.
# Cach dung:  ./run_tests.sh
set -euo pipefail
cd "$(dirname "$0")"

PORT=5000
BASE_URL="http://127.0.0.1:${PORT}"

# 1) Cai dependency neu thieu
python3 -c "import flask" 2>/dev/null || python3 -m pip install -q -r requirements.txt
command -v newman >/dev/null 2>&1 || npm install -g newman

# 2) Bat Flask o background, tu tat khi script ket thuc
python3 app.py >flask.log 2>&1 &
FLASK_PID=$!
trap 'kill "$FLASK_PID" 2>/dev/null || true' EXIT

# 3) Cho API san sang (toi da ~10 giay)
for _ in $(seq 1 50); do
  if curl -fs "${BASE_URL}/health" >/dev/null 2>&1; then break; fi
  sleep 0.2
done
curl -fs "${BASE_URL}/health" >/dev/null || { echo "Flask khong khoi dong duoc, xem flask.log"; exit 1; }

# 4) Chay collection bang Newman, xuat JUnit
newman run books-api.postman_collection.json \
  -e staging.postman_environment.json \
  -r cli,junit \
  --reporter-junit-export junit.xml
