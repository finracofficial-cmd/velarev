# -*- coding: utf-8 -*-
"""Judge.me の内部商品IDを解決し、CSVを詰め直す / レビューを直接投稿する。

Judge.me のインポートウィザードが照合に使う product_id は Judge.me 内部のIDで、
Shopify の商品ID ではない。CSV に Shopify の ID を入れても一致しないため、
まず external_id -> 内部ID を引いてから使う必要がある。

APIトークンは引数ではなく環境変数から読む。シェル履歴に残さないこと。

    export JUDGEME_API_TOKEN='...'          # Judge.me の Settings で発行した private token
    export JUDGEME_SHOP_DOMAIN='gvc1q8-j8.myshopify.com'

使い方:

    # 1. 内部IDを解決してキャッシュに保存（中断しても再実行で続きから）
    python3 tools/judgeme_sync.py resolve data/judgeme_reviews.csv

    # 2a. 内部IDを詰めたCSVを書き出す（ウィザードで取り込む場合）
    python3 tools/judgeme_sync.py rewrite data/judgeme_reviews.csv data/judgeme_reviews_internal.csv

    # 2b. API から直接投稿する（ウィザードを使わない場合）
    python3 tools/judgeme_sync.py post data/judgeme_reviews.csv
    python3 tools/judgeme_sync.py post data/judgeme_reviews.csv --live   # 実際に投稿

post は --live を付けない限り送信しない。まず付けずに実行して件数を確認すること。
"""
import csv, json, os, sys, time, urllib.error, urllib.parse, urllib.request

API = "https://api.judge.me/api/v1"
CACHE = "judgeme_product_ids.json"
TOKEN = os.environ.get("JUDGEME_API_TOKEN", "")
SHOP = os.environ.get("JUDGEME_SHOP_DOMAIN", "")


def need_env():
    missing = [k for k, v in (("JUDGEME_API_TOKEN", TOKEN), ("JUDGEME_SHOP_DOMAIN", SHOP)) if not v]
    if missing:
        sys.exit("環境変数が未設定: %s" % ", ".join(missing))


def call(method, path, params=None, form=None, tries=5):
    """Judge.me API を叩く。429/5xx は指数バックオフで再試行。"""
    params = dict(params or {}, shop_domain=SHOP, api_token=TOKEN)
    url = "%s%s?%s" % (API, path, urllib.parse.urlencode(params))
    data = urllib.parse.urlencode(form).encode() if form else None
    for attempt in range(tries):
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("X-Api-Token", TOKEN)
        if data:
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode() or "{}")
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            if e.code in (429, 500, 502, 503, 504) and attempt < tries - 1:
                wait = 2 ** attempt
                print("   %s -> %ds 待って再試行" % (e.code, wait), file=sys.stderr)
                time.sleep(wait)
                continue
            raise SystemExit("API %s %s: %s" % (e.code, path, body))
        except urllib.error.URLError as e:
            if attempt < tries - 1:
                time.sleep(2 ** attempt)
                continue
            raise SystemExit("接続失敗: %s" % e)


def load_cache():
    return json.load(open(CACHE)) if os.path.exists(CACHE) else {}


def save_cache(c):
    json.dump(c, open(CACHE, "w"), ensure_ascii=False, indent=0)


def resolve(csv_path):
    """CSV に出てくる Shopify 商品ID を Judge.me 内部IDへ解決してキャッシュする。"""
    need_env()
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    externals = sorted({r["product_id"] for r in rows if r.get("product_id")})
    cache = load_cache()
    todo = [e for e in externals if e not in cache]
    print("対象 %d 商品 / 解決済み %d / 未解決 %d" % (len(externals), len(externals) - len(todo), len(todo)))

    for i, ext in enumerate(todo, 1):
        res = call("GET", "/products/-1", {"external_id": ext})
        prod = res.get("product") or {}
        internal = prod.get("id")
        if internal:
            cache[ext] = internal
        else:
            cache[ext] = None
            print("   解決できず: %s" % ext, file=sys.stderr)
        if i % 25 == 0:
            save_cache(cache)
            print("   %d/%d" % (i, len(todo)))
        time.sleep(0.25)

    save_cache(cache)
    ok = sum(1 for v in cache.values() if v)
    print("解決 %d / 失敗 %d -> %s" % (ok, len(cache) - ok, CACHE))


def rewrite(src, dst):
    """内部IDを product_id に詰めたCSVを書き出す。"""
    cache = load_cache()
    if not cache:
        sys.exit("先に resolve を実行してください")
    rows = list(csv.DictReader(open(src, encoding="utf-8")))
    kept, dropped = [], 0
    for r in rows:
        internal = cache.get(r.get("product_id", ""))
        if not internal:
            dropped += 1
            continue
        r["product_id"] = internal
        kept.append(r)
    with open(dst, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(kept)
    print("書き出し %d 件 / 除外 %d 件 -> %s" % (len(kept), dropped, dst))
    if dropped:
        print("除外分は内部IDが引けなかった商品です。resolve のログを確認してください。")


def post(csv_path, live=False):
    """レビューを API から直接投稿する。"""
    need_env()
    # 投稿は platform=shopify + Shopify 商品ID で紐づく。内部IDは使わないので
    # resolve は不要（内部IDが要るのはウィザード用CSVを作る rewrite のときだけ）。
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8")))
    ready = [(r, r["product_id"]) for r in rows if r.get("product_id")]
    print("投稿対象 %d 件 / 商品ID欠落のため除外 %d 件" % (len(ready), len(rows) - len(ready)))
    if not live:
        print("これは確認のみです。実際に投稿するには --live を付けてください。")
        for r, pid in ready[:3]:
            print("   例) product=%s rating=%s %s / %s" % (pid, r["rating"], r["reviewer_name"], r["title"]))
        return

    done_path = "judgeme_posted.log"
    done = set(open(done_path).read().split()) if os.path.exists(done_path) else set()
    log = open(done_path, "a")
    sent = 0
    for i, (r, pid) in enumerate(ready, 1):
        key = "%s:%s" % (pid, r["reviewer_email"])
        if key in done:
            continue
        # API が受け付けるのは name / email。reviewer_name, reviewer_email では 422 になる。
        # 商品への紐付けは platform と id（Shopify 商品ID）の組。external_id /
        # product_external_id / product_handle はいずれも 201 を返すが
        # product_external_id=0 の未紐付けレビューになる。
        form = {
            "platform": "shopify",
            "id": pid,
            "name": r["reviewer_name"],
            "email": r["reviewer_email"],
            "rating": r["rating"],
            "title": r["title"],
            "body": r["body"],
        }
        if r.get("review_date"):
            form["created_at"] = r["review_date"]
        call("POST", "/reviews", form=form)
        log.write(key + "\n")
        log.flush()
        sent += 1
        if sent % 25 == 0:
            print("   %d/%d 投稿" % (i, len(ready)))
        time.sleep(0.3)
    print("投稿完了 %d 件（既存スキップ %d 件）" % (sent, len(ready) - sent))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    cmd = sys.argv[1]
    if cmd == "resolve":
        resolve(sys.argv[2])
    elif cmd == "rewrite":
        rewrite(sys.argv[2], sys.argv[3])
    elif cmd == "post":
        post(sys.argv[2], "--live" in sys.argv)
    else:
        sys.exit(__doc__)
