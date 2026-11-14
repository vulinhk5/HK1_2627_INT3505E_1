import argparse
import os
import sys
import threading
import time

from flask import g, jsonify, request  
from app import app                    

POOL_SIZE = int(os.getenv("POOL_SIZE", "5"))
DB_LATENCY = float(os.getenv("DB_LATENCY_MS", "50")) / 1000
POOL_TIMEOUT = float(os.getenv("POOL_TIMEOUT", "2"))
_pool = threading.BoundedSemaphore(POOL_SIZE)


@app.before_request
def acquire_connection():
    if request.path == "/health":
        return None
    if not _pool.acquire(timeout=POOL_TIMEOUT):
        return jsonify(code="POOL_TIMEOUT", message=f"no free DB connection (pool={POOL_SIZE})"), 503
    g.has_conn = True
    time.sleep(DB_LATENCY)         
    return None


@app.teardown_request
def release_connection(_exc):
    if g.pop("has_conn", False):
        _pool.release()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5001)
    port = ap.parse_args().port
    print(f"what-if: pool={POOL_SIZE} latency={DB_LATENCY*1000:.0f}ms timeout={POOL_TIMEOUT}s port={port}", flush=True)
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
