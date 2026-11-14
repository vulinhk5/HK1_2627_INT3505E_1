import os
import random

import requests
from locust import HttpUser, between, events, task

DEFAULT_HOST = "http://localhost:5000"

LIST_PATH = "/books"            # GET  /books              -> [ {id,title,author}, ... ]  (không phân trang)
DETAIL_PATH = "/books/{id}"     # GET  /books/<id>         -> chi tiết 1 cuốn
SEARCH_PATH = "/books"          # GET  /books?year=<year>  -> tìm theo năm (app Lab 3 bỏ qua param này)
SEARCH_PARAM = "year"
CREATE_PATH = "/books"          # POST /books              -> {"title": (bắt buộc), "author"} -> 201

ENABLE_WRITES = os.getenv("ENABLE_WRITES", "1") == "1"   # đặt 0 nếu API không có POST
YEARS = list(range(1990, 2025))
FALLBACK_IDS = list(range(1, 11))   # dùng khi không đọc được id từ GET /books

SEARCH_FAIL_RATE = 0.01

SLO_P95_MS = float(os.getenv("SLO_P95_MS", "300"))

SLO_MAX_FAIL_RATIO = float(os.getenv("SLO_MAX_FAIL_RATIO", "0.01"))

BOOK_IDS: list = []


def _extract_ids(payload) -> list:
    """Lấy danh sách id từ response, chịu được cả dạng [..] lẫn {"books": [..]}."""
    if isinstance(payload, dict):
        payload = next((v for v in payload.values() if isinstance(v, list)), [])
    if not isinstance(payload, list):
        return []
    return [b["id"] for b in payload if isinstance(b, dict) and "id" in b]


@events.test_start.add_listener
def load_book_ids(environment, **_):
    global BOOK_IDS
    host = (environment.host or DEFAULT_HOST).rstrip("/")
    try:
        r = requests.get(host + LIST_PATH, timeout=5)
        BOOK_IDS = _extract_ids(r.json())
    except Exception:
        BOOK_IDS = []
    if not BOOK_IDS:
        BOOK_IDS = FALLBACK_IDS
        print(f"[locustfile] Không đọc được id từ {host}{LIST_PATH}, dùng {FALLBACK_IDS}")


class BooksUser(HttpUser):
    host = DEFAULT_HOST
    wait_time = between(0.5, 1.5)   

    @task(4)
    def list_books(self):
        self.client.get(LIST_PATH, name="GET /books")

    @task(3)
    def get_book(self):
        book_id = random.choice(BOOK_IDS or FALLBACK_IDS)
        self.client.get(DETAIL_PATH.format(id=book_id), name="GET /books/[id]")

    @task(2)
    def search_by_year(self, year=None):
        year = year or random.choice(YEARS)
        with self.client.get(
            SEARCH_PATH,
            params={SEARCH_PARAM: year},
            name="GET /books?year=[year]",
            catch_response=True,
        ) as resp:
            if random.random() < SEARCH_FAIL_RATE:
                resp.failure("Simulated 500 Internal Server Error (1% fail rate)")
            elif resp.status_code != 200:
                resp.failure(f"HTTP {resp.status_code}")
            else:
                resp.success()

    @task(1)
    def create_book(self):
        if not ENABLE_WRITES:
            return
        payload = {
            "title": f"Locust book {random.randint(1, 10**6)}",
            "author": "Locust Bot",
        }
        with self.client.post(CREATE_PATH, json=payload, name="POST /books",
                              catch_response=True) as resp:
            if resp.status_code in (200, 201):
                resp.success()
                try:  
                    BOOK_IDS.append(resp.json()["id"])
                except (ValueError, KeyError, TypeError):
                    pass
            else:
                resp.failure(f"HTTP {resp.status_code}")


@events.quitting.add_listener
def ci_gate(environment, **_):
    if os.getenv("CI_GATE") != "1":
        return
    total = environment.stats.total
    p95 = total.get_response_time_percentile(0.95) or 0
    fail_ratio = total.fail_ratio
    problems = []
    if p95 >= SLO_P95_MS:
        problems.append(f"p95={p95:.0f}ms >= {SLO_P95_MS:.0f}ms")
    if fail_ratio > SLO_MAX_FAIL_RATIO:
        problems.append(f"fail_ratio={fail_ratio:.2%} > {SLO_MAX_FAIL_RATIO:.2%}")
    if problems:
        print("[CI GATE] FAIL: " + "; ".join(problems))
        environment.process_exit_code = 1
    else:
        print(f"[CI GATE] PASS: p95={p95:.0f}ms, fail_ratio={fail_ratio:.2%}")
        environment.process_exit_code = 0
