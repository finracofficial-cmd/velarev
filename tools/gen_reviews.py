# -*- coding: utf-8 -*-
"""VELA / Judge.me インポート用ダミーレビュー生成器。

出力データは全て架空。実在の購入者・実注文には基づかない。
パスワード保護下のストアでの表示確認用。
各レビューは対象商品の説明文・サイズ表・バリエーションを読み取って生成する。
"""
import csv, html, json, random, re, sys, unicodedata
from datetime import date, timedelta

NAMES = ["ハルカ","ミナ","リオ","アオイ","ユナ","ナナ","サキ","カレン","モモ","ヒナ","マリン","アカリ","ノア","セナ","ミオ","ユイ","ソラ","コハル","リコ","マナ","アヤ","チヒロ","ナギサ","スミレ","ホノカ","ルナ","エマ","シオリ","カナ","ミク","ツムギ","イロハ","サラ","ミサキ","ユキ","レイ","アンナ","ナオ","マイ","キョウカ","フウカ","リン","ココ","アイ","ヒヨリ","マオ","ユメ","ニナ","サヤ","トワ"]

CATS = [("水着",["ビキニ","水着","スイム"]),("アウター",["アウター","ジャケット","コート","ブルゾン"]),
        ("ニット",["ニット","セーター","カーディガン"]),("セットアップ",["セットアップ"]),
        ("ワンピース",["ワンピース","ドレス"]),("スカート",["スカート"]),
        ("パンツ",["パンツ","ショートパンツ","デニムパンツ","レギンス"]),
        ("キャミソール",["キャミソール","タンクトップ","ベアトップ"]),
        ("トップス",["トップス","Tシャツ","シャツ","ブラウス"])]

SIZE_KEYS = ["着丈","バスト","胸囲","ウエスト","ヒップ","肩幅","袖丈","総丈","股下","スカート丈","パンツ丈"]
SIZE_H = {"XS":(146,154),"S":(148,158),"M":(155,165),"L":(162,172),"XL":(165,174),"F":(150,170),"フリー":(150,170)}

# 説明文から拾う特徴語 -> レビューでの言及文
FEATURE_LINE = {
 "レース":"レースの繊細さが写真以上でした","フリル":"フリルのボリュームがちょうど良いです","リボン":"リボンの位置が可愛くて気に入りました",
 "花柄":"花柄が派手すぎず上品でした","フローラル":"花柄が派手すぎず上品でした","ドット":"ドット柄の大きさがちょうど良いです",
 "チェック":"チェック柄の色合いが落ち着いていました","ストライプ":"ストライプの幅がちょうど良いです",
 "デニム":"デニムの色落ち加減が good でした","サテン":"サテンの光沢が上品でチープに見えません",
 "ニット":"編み地がしっかりしていて安っぽくありません","透け":"透け感は控えめでインナー次第で調整できます",
 "シアー":"シアー感が上品で着やすいです","パフスリーブ":"パフスリーブのふくらみが可愛いです",
 "オフショル":"肩の出方がちょうど良いバランスでした","ギャザー":"ギャザーの寄せ方がきれいです",
 "プリーツ":"プリーツがしっかりついていて動くたびにきれいです","スリット":"スリットの深さは歩きやすい範囲でした",
 "刺繍":"刺繍が丁寧で高見えします","ビジュー":"ビジューの輝きが上品でした",
 "クロシェ":"クロシェ編みの質感が可愛いです","メッシュ":"メッシュの目が細かくて上品でした",
 "ハイウエスト":"ハイウエストで脚が長く見えます","Aライン":"Aラインのシルエットがきれいに出ます",
 "ホルターネック":"ホルターネックで首まわりがすっきり見えます","カットアウト":"カットアウトの位置が絶妙でした",
 "リブ":"リブの伸縮がよくて着心地が良いです","ケーブル":"ケーブル編みが立体的で可愛いです",
 "コーデュロイ":"コーデュロイの畝がきれいでした","ツイード":"ツイードの織りが上品で高見えします",
 "ベロア":"ベロアの起毛が上品でした","チュール":"チュールの重なりが可愛いです",
 "アシンメトリー":"左右非対称のデザインが効いています","レトロ":"レトロな雰囲気が可愛いです",
 "ヴィンテージ":"ヴィンテージ感のある色味が気に入りました","バンドゥ":"バンドゥ部分がずれにくくて安心です",
 "ワッフル":"ワッフル地の凹凸が可愛いです","刺し子":"生地の織りが丁寧でした",
}
FIT_WORDS = {"ゆったり":"ゆとりがあって締めつけ感がありません","ルーズ":"ルーズなシルエットで体型を拾いません",
             "オーバーサイズ":"オーバーサイズですが着られている感じにはなりません","タイト":"タイトですが窮屈さはありません",
             "スリム":"体のラインがきれいに出ます","体型カバー":"気になる部分を自然にカバーしてくれます",
             "フィット":"ほどよくフィットしてきれいに見えます"}

OPEN = {"トップス":["形がきれいで一枚で決まります","合わせやすくて出番が多そうです","顔まわりが明るく見えます"],
 "キャミソール":["一枚でもインナーとしても使えます","肩紐の位置がちょうど良かったです","重ね着の幅が広がりました"],
 "スカート":["シルエットがきれいに落ちます","丈感がちょうど良かったです","一枚で雰囲気が出ます"],
 "パンツ":["動きやすくて助かります","腰まわりが楽でした","カジュアルすぎず履けます"],
 "ワンピース":["一枚で着られるので楽です","スタイルよく見えます","シーンを選ばず着られそうです"],
 "ニット":["厚すぎず長い期間着られそうです","肌ざわりが良くてチクチクしません","一枚で着ても様になります"],
 "アウター":["羽織るだけで様になります","思ったより軽くて着やすいです","季節の変わり目に重宝しそうです"],
 "セットアップ":["上下揃っているので迷わず着られます","セットでも単品でも使えます","色味が揃っていて統一感があります"],
 "水着":["デザインが可愛くて気分が上がります","露出が高すぎず着やすいです","羽織りと合わせやすいです"],
 "アイテム":["思っていたより丁寧な作りでした","合わせやすくて出番が多そうです","雰囲気が出て気に入りました"]}
STYLE = {"トップス":["デニムに合わせるだけで決まりました","スカートに合わせると女性らしくなります","羽織りものとの相性も良さそうです"],
 "キャミソール":["シャツを羽織って抜け感を出しています","ハイウエストのボトムスと合わせています","カーディガンと重ねても可愛いです"],
 "スカート":["シンプルなトップスを合わせるだけで成立します","スニーカーでも綺麗めでも合わせられます","タイツを合わせれば秋冬もいけそうです"],
 "パンツ":["コンパクトなトップスと相性が良いです","スニーカーでラフに履いています","ヒールを合わせると綺麗めになります"],
 "ワンピース":["羽織りものを足せば長く着られそうです","小物次第で印象を変えられます","そのままでも十分様になります"],
 "ニット":["ロングスカートと合わせるのが気に入っています","インナーを足して重ね着もできます","パンツでもスカートでも合います"],
 "アウター":["シンプルな中身でもこれ一枚で決まります","丈の短いトップスと相性が良いです","色味が落ち着いているので合わせやすいです"],
 "セットアップ":["セットで着ると一気にまとまります","トップスだけ単品でも使えそうです","小物を足すと印象が変わります"],
 "水着":["羽織りとサンダルで海でも街でもいけます","日焼け対策の羽織りと合わせています","小物を足して雰囲気を変えています"],
 "アイテム":["手持ちの服とすぐ合わせられました","合わせるものを選ばないのが良いです","小物次第で印象を変えられます"]}
CLOSE = ["また色違いも欲しくなりました。","この価格でこの質感なら満足です。","リピートしたいと思える一枚です。","買ってよかったです。","友達にも聞かれました。","出番が多くなりそうです。","期待どおりでした。","長く着られそうです。"]
TITLES = ["可愛いです","お気に入りになりました","期待どおりでした","写真どおりでした","買ってよかった","雰囲気が可愛い","使いやすいです","リピートしたいです","丈感がちょうどいい","色味が可愛い","高見えします","着心地が良いです"]

def plain(body_html):
    t = re.sub(r"<[^>]+>", " ", body_html or "")
    return html.unescape(" ".join(t.split()))

def category(tags):
    t = set(tags)
    for name, keys in CATS:
        if t & set(keys): return name
    return "アイテム"

def parse_size_chart(body_html):
    text = unicodedata.normalize("NFKC", plain(body_html))
    m = re.search(r"サイズ((?:\s*(?:%s))+)(.*)$" % "|".join(SIZE_KEYS), text)
    if not m: return {}
    cols = re.findall("|".join(SIZE_KEYS), m.group(1))
    chart = {}
    for sm in re.finditer(r"(?<![A-Za-z])(XS|S|M|L|XL|XXL|2XL|3XL|F)(?![A-Za-z])((?:\s*\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?)+)", m.group(2)):
        cms = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*/", sm.group(2))]
        if cms: chart[sm.group(1)] = dict(zip(cols, cms))
    return chart

GARMENT = r"(Dress|Coat|Vest|Top|Jacket|Skirt|Pants|Shirt|Set|Suit|Cardigan|Bottom|ワンピース|コート|ベスト|トップス|ジャケット|スカート|パンツ|シャツ|セット|上|下)"

def clean_color(c):
    """バリエーション名から衣類名を除き、色名として使えるものだけ返す。"""
    c = re.sub(r"[（(].*?[)）]", "", c).strip()
    c = re.sub(r"\s*" + GARMENT + r"\s*$", "", c, flags=re.I).strip()
    c = re.sub(r"^\s*" + GARMENT + r"\s*", "", c, flags=re.I).strip()
    if not c or len(c) > 12 or re.search(GARMENT, c, re.I): return None
    return c

def variant_axes(variants):
    colors, sizes = [], []
    for v in variants:
        for p in [x.strip() for x in (v.get("title") or "").split("/")]:
            if re.fullmatch(r"XS|S|M|L|XL|XXL|2XL|3XL|F|フリー", p):
                if p not in sizes: sizes.append(p)
            elif p and p.lower() != "default title":
                c = clean_color(p)
                if c and c not in colors: colors.append(c)
    return colors, sizes

def product_notes(prod):
    """商品説明・タイトル・タグから、この商品固有の言及文を集める。"""
    blob = prod["title"] + " " + plain(prod.get("body_html")).split("■")[0] + " " + " ".join(prod.get("tags", []))
    feats = [FEATURE_LINE[k] for k in FEATURE_LINE if k in blob]
    fits  = [FIT_WORDS[k] for k in FIT_WORDS if k in blob]
    # 重複除去（同じ文面になる特徴語があるため）
    return list(dict.fromkeys(feats)), list(dict.fromkeys(fits))

def build(prod, idx, rng, cat, chart, colors, sizes, feats, fits, used_titles, used_open):
    size = rng.choice(sizes) if sizes else "F"
    lo, hi = SIZE_H.get(size, (150, 170))
    height = rng.randrange(lo, hi + 1)

    op_pool = [o for o in OPEN[cat] if o not in used_open] or OPEN[cat]
    opener = rng.choice(op_pool); used_open.add(opener)
    parts = [opener]
    if feats:
        parts.append(feats[idx % len(feats)])

    SANE = {"着丈":(35,140),"総丈":(35,150),"ウエスト":(55,95),"バスト":(70,115),"胸囲":(70,115),"肩幅":(28,55)}
    facts = []
    row = chart.get(size, {})
    for key in ("着丈","ウエスト","バスト","胸囲","総丈","肩幅"):
        if key in row:
            lo_v, hi_v = SANE[key]
            if lo_v <= row[key] <= hi_v:
                facts.append("%s%gcm" % (key, row[key]))
        if len(facts) == 2: break
    if facts:
        parts.append("%dcmで%s、%sは表記どおりでした" % (height, size, "・".join(facts)))
    else:
        parts.append("%dcmで%sを着用してちょうど良かったです" % (height, size))

    if fits:
        parts.append(fits[idx % len(fits)])
    if colors and idx == 0:
        parts.append("色は%sを選びました" % rng.choice(colors))
    parts.append(rng.choice(STYLE[cat]))

    body = "。".join(p.rstrip("。") for p in parts) + "。" + rng.choice(CLOSE)

    pool = [t for t in TITLES if t not in used_titles] or TITLES
    title = rng.choice(pool)
    used_titles.add(title)
    return rng.choice(NAMES), title, body

def main(src, out, per=2, seed=20260820):
    prods = json.load(open(src))
    start = date(2026, 3, 1); span = (date(2026, 8, 10) - start).days
    rows = []
    for p in prods:
        rng = random.Random("%d:%s" % (seed, p["handle"]))
        cat = category(p.get("tags", []))
        chart = parse_size_chart(p.get("body_html"))
        colors, sizes = variant_axes(p.get("variants", []))
        feats, fits = product_notes(p)
        used_titles, used_names, used_open = set(), set(), set()
        for i in range(per):
            for _ in range(8):
                name, title, body = build(p, i, rng, cat, chart, colors, sizes, feats, fits, used_titles, used_open)
                if name not in used_names: break
            used_names.add(name)
            rows.append({"product_handle": p["handle"], "reviewer_name": name,
                "reviewer_email": "%s-%d@example.invalid" % (p["handle"][:24], i + 1),
                "review_title": title, "review_body": body, "rating": 5,
                "review_date": (start + timedelta(days=rng.randrange(span))).isoformat(),
                "verified_buyer": "true",
                "product_url": "https://vela-vela.com/products/%s" % p["handle"]})
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        f.write("# 注意: このCSVの全レビューは架空のテストデータです。実在の購入者・実注文には基づきません。\n")
        f.write("# verified_buyer=true も実際の購入実績に基づくものではありません。\n")
        f.write("# パスワード保護されたストアでの表示確認専用。保護を解除する場合は事前に全件削除してください。\n")
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("products=%d reviews=%d -> %s" % (len(prods), len(rows), out))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2)
