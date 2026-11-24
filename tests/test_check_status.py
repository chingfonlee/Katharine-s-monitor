"""?冽璈芋?砌撩?皜祈岫 check_status.py??
璅⊥隡箸??典??喟? HTML 靘 kaofarmers.tw ?祕??蝣潛?蝯?嚗?銝行芋?研ol.54嚗paper/66嚗? Vol.53嚗paper/65嚗??芣??蝡汗閮?具?甈?GET +1??銵??"""
import csv
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ["NO_PROXY"] = "127.0.0.1,localhost"
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import check_status  # noqa: E402

COUNTERS = {"66": 14603, "65": 46533}
LOCK = threading.Lock()

PAGE = """<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8" />
<title>?嗆???-?噙?祈-?噙憭扯??/title></head><body>
<div class="btn-group social_share" role="group">
  <span class="py-3 me-2 text-secondary"><i class="fas fa-share-alt"></i>?澈??/span>
  <a class="btn btn-line" href="#">LINE</a>
</div>
<span class="py-3 text-secondary">
  <i class="fas fa-eye"></i>{views}甈?</span>
<h3>??璅?</h3>
<article><p>???潸牧嚗??????甈∠?撽蝚?甈∠宏???望鈭?00甈∟?蝞晞?/p></article>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.endswith("/missing"):
            self.send_response(404)
            self.end_headers()
            return
        issue_key = "65" if "/epaper/65" in self.path else "66"
        with LOCK:
            COUNTERS[issue_key] += 1
            n = COUNTERS[issue_key]
        body = PAGE.replace("{views}", str(n)).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def main():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"

    # --- ?桀?皜祈岫嚗?祕?瑕??啁??挾 ---
    real = '<span class="py-3 text-secondary"><i class="fas fa-eye"></i>14603甈?/span>'
    assert check_status.extract_views(real) == 14603
    assert check_status.extract_views("<p>瘝?閮?剁??芣?蝚?甈?/p>") is None
    assert check_status.extract_views('<i class="fas fa-eye"></i>1,234甈?) == 1234
    assert len(check_status.ISSUES["Vol.54"]) == 13
    assert len(check_status.ISSUES["Vol.53"]) == 13
    assert len(check_status.URLS) == 26
    print("extract_views ??26 蝬脣?閮剖??桀?皜祈岫嚗?")

    # --- ?游?皜祈岫嚗ol.54 (13) + Vol.53 (13) + 404 + ???銝?蝬脣? ---
    check_status.DELAY = 0.02
    test_issues = {
        "Vol.54": [
            f"{base}/farmer-colours/epaper/current-issue",
            *[f"{base}/farmer-colours/epaper/66/{n}" for n in range(560, 572)],
            f"{base}/farmer-colours/epaper/missing",
        ],
        "Vol.53": [
            f"{base}/farmer-colours/epaper/65",
            *[f"{base}/farmer-colours/epaper/65/{n}" for n in range(548, 560)],
            "http://127.0.0.1:1/closed-port",
        ],
    }
    os.chdir(os.path.dirname(__file__))
    if os.path.exists("view_history.csv"):
        os.remove("view_history.csv")

    ok = check_status.main(test_issues)
    assert ok is False

    with open("view_history.csv", "r", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))
    assert rows[0] == check_status.HISTORY_HEADER
    last = rows[-1]
    assert last[2] == "26" and last[3] == "28"
    assert last[4] == "14616", f"Expected Vol.54=14616, got {last[4]}"
    assert last[6] == "46546", f"Expected Vol.53=46546, got {last[6]}"
    print("???函?閮??view_history.csv ?游?皜祈岫嚗?")
    srv.shutdown()


if __name__ == "__main__":
    main()
