"""
اختبار الحمل/الإجهاد لخادم نبراس (المرحلة 11).

ينسخ قاعدة البيانات إلى مجلد مؤقت (حتى لا يُلمس الأصل)، يشغّل الخادم
على منفذ محلي عشوائي داخل نفس العملية، ثم يطلق عددًا متزامنًا من الطلبات
عبر ThreadPoolExecutor ويرصد: المعدل، نسبة النجاح، والتأخير p50/p95/p99.

الاستخدام:
    python scripts/load_test.py [--concurrency 32] [--requests 600]
                                [--db nibras.db] [--endpoints "health,texts,search"]

ملاحظة: الاستخدام افتراضي للقراءة فقط (بدون مصادقة). الردود 429 من حدود
المعدل تُعدّ "متوقعة" وليست فشلًا.
"""
import argparse
import http.client
import statistics
import sys
import tempfile
import threading
import time
import urllib.parse
from pathlib import Path

from werkzeug.serving import make_server

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

ENDPOINTS = {
    "health": "/api/health",
    "ready": "/api/ready",
    "categories": "/api/categories",
    "texts": "/api/texts",
    "text": "/api/texts/1",
    "article": "/api/articles/1",
    "calculators": "/api/calculators",
    "procedures": "/api/procedures",
    "marketplace": "/api/marketplace/templates",
    "professionals": "/api/professionals",
    "search": "/api/search?q=" + urllib.parse.quote("محاماة"),
    "ads": "/api/ads/serve?slot=directory_listing_top",
    "community": "/api/community/posts",
    "templates": "/api/documents/templates",
}


def _prepare_db(db_path: Path):
    """ينسخ قاعدة البيانات إلى مجلد مؤقت ويعيد المسار (تلقائي التنظيف)."""
    if not Path(db_path).exists():
        raise SystemExit(f"قاعدة البيانات غير موجودة: {db_path}")
    tmpdir = Path(tempfile.mkdtemp(prefix="nibras-loadtest-"))
    target = tmpdir / "nibras.db"
    with open(db_path, "rb") as src, open(target, "wb") as dst:
        dst.write(src.read())
    return target


def _start_server(db_path: Path, port: int):
    from app import database

    database.DB_PATH = Path(db_path)
    from app import create_app

    app = create_app()
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def _wait_until_ready(port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            conn.request("GET", "/api/health")
            resp = conn.getresponse()
            resp.read()
            conn.close()
            if resp.status == 200:
                return
        except OSError:
            time.sleep(0.05)
    raise SystemExit("لم يتمكن الخادم من الإقلاع خلال المهلة")


def _run(port: int, endpoints, total: int, concurrency: int):
    from queue import Empty, Queue

    q = Queue()
    lock = threading.Lock()
    counter = {"done": 0, "2xx": 0, "429": 0, "other": 0}
    latencies = {name: [] for name in endpoints}

    def worker():
        while True:
            try:
                name, path = q.get_nowait()
            except Empty:
                return
            start = time.perf_counter()
            try:
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=15)
                conn.request("GET", path)
                resp = conn.getresponse()
                resp.read()
                conn.close()
                status = resp.status
            except (OSError, http.client.HTTPException):
                status = 0
            elapsed = (time.perf_counter() - start) * 1000
            latencies[name].append(elapsed)
            with lock:
                counter["done"] += 1
                if 200 <= status < 300:
                    counter["2xx"] += 1
                elif status == 429:
                    counter["429"] += 1
                else:
                    counter["other"] += 1
            q.task_done()

    pairs = [(name, ENDPOINTS[name]) for name in endpoints]
    for i in range(total):
        q.put(pairs[i % len(pairs)])
    workers = [threading.Thread(target=worker, daemon=True) for _ in range(concurrency)]
    start = time.perf_counter()
    for t in workers:
        t.start()
    q.join()
    duration = time.perf_counter() - start

    flat = []
    for lst in latencies.values():
        flat.extend(lst)
    print(f"الطلبات: {counter['done']}  |  نجاح 2xx: {counter['2xx']}  |  429 متوقعة: {counter['429']}  |  أخرى: {counter['other']}")
    print(f"المدة: {duration:.2f} ثانية  |  المعدل: {counter['done'] / duration:.1f} طلب/ثانية")
    if flat:
        flat_sorted = sorted(flat)
        n = len(flat_sorted)
        p = lambda q_: flat_sorted[min(n - 1, int(q_ * n))]
        print(f"التأخير: p50 {p(0.50):.1f}ms | p95 {p(0.95):.1f}ms | p99 {p(0.99):.1f}ms | متوسط {statistics.mean(flat):.1f}ms")
    print("حسب المسار (متوسط/p95):")
    for name in endpoints:
        lst = sorted(latencies[name])
        if not lst:
            continue
        m = len(lst)
        p95 = lst[min(m - 1, int(0.95 * m))]
        print(f"  {name:14s} n={m:4d}  متوسط {statistics.mean(lst):6.1f}ms  p95 {p95:6.1f}ms")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="load_test.py", description="اختبار حمل نبراس")
    parser.add_argument("--concurrency", type=int, default=32)
    parser.add_argument("--requests", type=int, default=600)
    parser.add_argument("--db", default=str(REPO_ROOT / "nibras.db"))
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument(
        "--endpoints",
        default=",".join(ENDPOINTS.keys()),
        help="مفصولة بفواصل من: " + ",".join(ENDPOINTS.keys()),
    )
    args = parser.parse_args(argv)

    names = [n.strip() for n in args.endpoints.split(",") if n.strip()]
    unknown = [n for n in names if n not in ENDPOINTS]
    if unknown:
        raise SystemExit(f"مسارات غير معروفة: {unknown}")

    temp_db = _prepare_db(Path(args.db))
    # قياس الإنتاجية الخام دون ضجيج سجل كل طلب على شاشة القياس
    import os

    os.environ.setdefault("NIBRAS_LOG_ACCESS", "0")
    os.environ.setdefault("NIBRAS_LOG_LEVEL", "WARNING")
    port = args.port or 0
    server = _start_server(temp_db, port)
    port = server.server_port
    _wait_until_ready(port)
    print(f"الخادم جاهز على http://127.0.0.1:{port} (قاعدة مؤقتة: {temp_db})")
    _run(port, names, args.requests, args.concurrency)
    server.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
