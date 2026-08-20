# -*- coding: utf-8 -*-
"""vela-vela.com の公開カタログを全ページ取得して JSON に保存する。"""
import json, sys, time, urllib.request

def fetch(base="https://vela-vela.com", out="products_all.json"):
    products, page = [], 1
    while page <= 20:
        with urllib.request.urlopen("%s/products.json?limit=250&page=%d" % (base, page)) as r:
            batch = json.load(r).get("products", [])
        if not batch:
            break
        products.extend(batch)
        page += 1
        time.sleep(0.3)
    json.dump(products, open(out, "w"), ensure_ascii=False)
    print("products=%d -> %s" % (len(products), out))

if __name__ == "__main__":
    fetch(out=sys.argv[1] if len(sys.argv) > 1 else "products_all.json")
