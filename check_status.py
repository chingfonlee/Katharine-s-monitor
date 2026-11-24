"""???赤?噙?祈?餃???蝬脣?嚗ol.54 + Vol.53嚗??????臬?????汗甈⊥??
?冽?嚗?    pip install -r requirements.txt
    python check_status.py

瘜冽?嚗?- 蝬脩????嗅?????賂??隞仿ㄐ?餅???甈∩?????0.5 蝘?- ?汗甈⊥?胯??蝡??具?閮?剁?銝瘥??閮?嚗?  瘥赤????隞颱?銝? +1嚗?甇?Vol.54嚗?3 ????Vol.53嚗?3 ?????芷?憓?"""
from __future__ import annotations

import csv
import os
import re
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

ISSUES: dict[str, list[str]] = {
    "Vol.54": [
        "https://www.kaofarmers.tw/farmer-colours/epaper/current-issue",
        *[f"https://www.kaofarmers.tw/farmer-colours/epaper/66/{n}" for n in range(560, 572)],
    ],
    "Vol.53": [
        "https://www.kaofarmers.tw/farmer-colours/epaper/65",
        *[f"https://www.kaofarmers.tw/farmer-colours/epaper/65/{n}" for n in range(548, 560)],
    ],
}
URLS = [url for urls in ISSUES.values() for url in urls]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0 Safari/537.36"
    )
}
TIMEOUT = 15
DELAY = 0.5
RETRIES = 2

HISTORY_HEADER = ["?啁??", "閫貊?孵?", "?????", "蝬脣?蝮賣", "?祆??汗甈⊥", "憭望?蝬脣?", "Vol.53?汗甈⊥"]

# 撖行葫?? HTML嚗?span class="py-3 text-secondary"><i class="fas fa-eye"></i>14603甈?/span>
VIEW_RE = re.compile(r'fa-eye"\s*>\s*</i>\s*([\d,]+)\s*甈?)
VIEW_RE_FALLBACK = re.compile(r">\s*([\d,]+)\s*甈﹏s*<")


def extract_views(html: str) -> int | None:
    m = VIEW_RE.search(html)
    if not m:  # 蝬脩??寧????蝷箔?閬????湛?敺?鈭怠?憛?敺蝚砌??摮?甈～?        start = html.find("?澈??)
        m = VIEW_RE_FALLBACK.search(html, start if start != -1 else 0)
    return int(m.group(1).replace(",", "")) if m else None


def check(client: httpx.Client, url: str, issue: str = "") -> dict:
    error = ""
    for attempt in range(RETRIES + 1):
        try:
            r = client.get(url)
            ok = r.status_code == 200
            return {
                "?": issue,
                "url": url,
                "???": "??" if ok else "憭望?",
                "??Ⅳ": r.status_code,
                "?汗甈⊥": extract_views(r.text) if ok else None,
                "?航炊": "",
            }
        except httpx.HTTPError as e:
            error = f"{type(e).__name__}: {e}"
            if attempt < RETRIES:          # ?敺?甈∪仃?停銝??
                time.sleep(2 * (attempt + 1))
    return {"?": issue, "url": url, "???": "憭望?", "??Ⅳ": None, "?汗甈⊥": None, "?航炊": error}


def ensure_history_header(history_path: str) -> None:
    """蝣箔??Ｘ? view_history.csv ???單??啗”?哨?鋆??喳?唳?雿???""
    if not os.path.exists(history_path):
        with open(history_path, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(HISTORY_HEADER)
        return

    with open(history_path, "r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    if not rows:
        with open(history_path, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(HISTORY_HEADER)
        return

    if rows[0] != HISTORY_HEADER:
        upgraded = [HISTORY_HEADER]
        for row in rows[1:]:
            if len(row) < len(HISTORY_HEADER):
                row = row + [""] * (len(HISTORY_HEADER) - len(row))
            upgraded.append(row)
        with open(history_path, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(upgraded)


def main(issues: dict[str, list[str]] = ISSUES) -> bool:
    results: list[dict] = []
    with httpx.Client(headers=HEADERS, timeout=TIMEOUT, follow_redirects=True) as client:
        for issue_name, urls in issues.items():
            for url in urls:
                res = check(client, url, issue=issue_name)
                results.append(res)
                views_str = res["?汗甈⊥"] if res["?汗甈⊥"] is not None else "-"
                print(f"[{issue_name}] {res['???']}  {views_str:>8}  {url}  {res['?航炊']}")
                time.sleep(DELAY)

    now = datetime.now(ZoneInfo("Asia/Taipei"))   # GitHub ?脩垢銝餅???UTC嚗絞銝?典?????    out = f"views_{now:%Y%m%d_%H%M%S}.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=results[0].keys())
        w.writeheader()
        w.writerows(results)

    ok = sum(r["???"] == "??" for r in results)
    issue_stats: dict[str, tuple[int, int, int | None]] = {}
    for issue_name in issues:
        sub = [r for r in results if r["?"] == issue_name]
        sub_ok = sum(r["???"] == "??" for r in sub)
        sub_views = [r["?汗甈⊥"] for r in sub if r["?汗甈⊥"] is not None]
        issue_stats[issue_name] = (sub_ok, len(sub), max(sub_views) if sub_views else None)

    print(f"\n????? {ok}/{len(results)}")
    for issue_name, (sub_ok, sub_total, max_v) in issue_stats.items():
        if max_v is not None:
            print(f"{issue_name} ?汗甈⊥嚗max_v}嚗?? {sub_ok}/{sub_total}嚗甈⊥炎?亥甜??{sub_ok} 甈∴?")
    print(f"蝯?撌脣???{out}")

    # 蝝舐?甇瑕嚗?甈⊥炎?亥蕭??? view_history.csv嚗itHub 銝?鋡怠神??repo嚗?亦?敺嚗?    history = "view_history.csv"
    ensure_history_header(history)
    failed = [
        f"{r['?']}:{r['url'].rsplit('/', 1)[-1]}"
        for r in results
        if r["???"] != "??"
    ]
    vol54_max = issue_stats.get("Vol.54", (0, 0, None))[2]
    vol53_max = issue_stats.get("Vol.53", (0, 0, None))[2]
    with open(history, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            f"{now:%Y-%m-%d %H:%M:%S}",
            os.environ.get("GITHUB_EVENT_NAME", "local"),
            ok,
            len(results),
            vol54_max if vol54_max is not None else "",
            " ".join(failed),
            vol53_max if vol53_max is not None else "",
        ])
    print(f"甇瑕撌脰蕭? {history}")

    # ??GitHub Actions 銝銵?嚗?蝯?銵冽憿舐內?典銵??Ｖ?嚗?璈????堆?
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"## ?噙?祈???瑼Ｘ嚗now:%Y-%m-%d %H:%M} ?啁??嚗n\n")
            parts = [f"**????? {ok}/{len(results)}**"]
            for issue_name, (sub_ok, _, max_v) in issue_stats.items():
                if max_v is not None:
                    parts.append(f"**{issue_name} ?汗甈⊥嚗max_v}**嚗?{sub_ok}嚗?)
            f.write("?嚚".join(parts))
            f.write("\n\n| ? | 蝬脣? | ??? | ??Ⅳ | ?汗甈⊥ | ?航炊 |\n|---|---|---|---|---|---|\n")
            for r in results:
                v_str = r["?汗甈⊥"] if r["?汗甈⊥"] is not None else "-"
                f.write(
                    f"| {r['?']} | {r['url']} | {r['???']} | {r['??Ⅳ'] or '-'} | "
                    f"{v_str} | {r['?航炊'] or ''} |\n"
                )

    return ok == len(results)


if __name__ == "__main__":
    # ?遙雿雯?憭望?撠曹誑?航炊蝣潛???GitHub ???活?瑁?璅?憭望?銝血?靽⊿
    sys.exit(0 if main() else 1)
