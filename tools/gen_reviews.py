# -*- coding: utf-8 -*-
"""VELA / Judge.me インポート用ダミーレビュー生成器。

出力データは全て架空。実在の購入者・実注文には基づかない。
パスワード保護下のストアでの表示確認用。

文体を1つの型に固定すると、何件並べても同じ文章に見える。そのため
複数の型（短文・サイズ重視・素材重視・箇条書き など）を用意し、
1件ごとに別の型を割り当てる。身長や着用サイズに触れるのは一部の型だけ。
本文が既出のものと一致した場合は引き直して、全件で重複を出さない。
"""
import csv, html, json, random, re, sys, unicodedata
from datetime import date, timedelta

MAX_LEN = 110          # これを超える本文は引き直す
UNIQUE_TRIES = 60      # 重複回避の試行回数

# ---------------------------------------------------------------- 投稿者名
NAMES_KATA = ["ハルカ","ミナ","リオ","アオイ","ユナ","ナナ","サキ","カレン","モモ","ヒナ",
              "マリン","アカリ","ノア","セナ","ミオ","ユイ","ソラ","コハル","リコ","マナ",
              "アヤ","チヒロ","ナギサ","スミレ","ホノカ","ルナ","エマ","シオリ","カナ","ミク",
              "ツムギ","イロハ","サラ","ミサキ","レイ","アンナ","ナオ","マイ","フウカ","リン",
              "ココ","アイ","ヒヨリ","マオ","ユメ","ニナ","サヤ","トワ","キョウカ","ホタル"]
NAMES_HIRA = ["はるか","みな","ゆい","あおい","なな","もも","ひなの","さき","りん","ここ",
              "まな","あかり","ちひろ","すみれ","ゆきの","みお","ののか","つむぎ","さくら",
              "いちか","こはる","えま","ひなた","あさひ"]
NAMES_ROMA = ["Yui","Mina","Aoi","Nana","Rio","Sena","Karen","Momo","Haruka","Luna",
              "Emi","Saki","Kana","Miku","Riko","Nao","Mei","Ayu"]
NAMES_INIT = ["M.K","Y.S","A.T","R.N","K","N.H","S.Y","mii","non","ちー","ぴよ","もか",
              "R","H.M","yu","なぎ","くま","ぷー"]

EMOJI_CUTE = ["🎀","🥺","💕","🩷","✨","🫶","😍","☺️","🌸","💗","🤍","🥰","💐","🍒"]
EMOJI_PLAIN = ["👍","😊","🙆‍♀️","✨","👗","🫧","🙌","👌"]

# ---------------------------------------------------------------- カテゴリ
CATS = [("水着",       ["ビキニ","水着","スイム"]),
        ("アウター",   ["アウター","ジャケット","コート","ブルゾン"]),
        ("ニット",     ["ニット","セーター","カーディガン"]),
        ("セットアップ",["セットアップ"]),
        ("ワンピース", ["ワンピース","ドレス"]),
        ("スカート",   ["スカート"]),
        ("パンツ",     ["パンツ","ショートパンツ","デニムパンツ","レギンス"]),
        ("キャミソール",["キャミソール","タンクトップ","ベアトップ"]),
        ("トップス",   ["トップス","Tシャツ","シャツ","ブラウス"])]

SIZE_KEYS = ["着丈","バスト","胸囲","ウエスト","ヒップ","肩幅","袖丈","総丈","股下","スカート丈","パンツ丈"]
SIZE_H = {"XS":(146,154),"S":(148,158),"M":(155,165),"L":(162,172),"XL":(165,174),
          "F":(150,170),"フリー":(150,170)}
SANE = {"着丈":(35,140),"総丈":(35,150),"ウエスト":(55,95),"バスト":(70,115),
        "胸囲":(70,115),"肩幅":(28,55),"袖丈":(15,70)}

FEATURES = {
 "レース":["レースが上品","レースの透け感が絶妙","レースが安っぽくない","レース部分がとにかく可愛い",
        "レースが細かくて高見えする","レースの主張が強すぎない"],
 "フリル":["フリルの量がちょうどいい","フリルが甘すぎない","フリルにボリュームがある",
        "フリルの落ち方がきれい","フリルが子どもっぽくならない"],
 "リボン":["リボンが主役","リボンの位置が絶妙","リボンが取り外せたらもっと良かったけど可愛い",
        "リボンのサイズ感がちょうどいい","リボンがしっかり縫い付けてある"],
 "花柄":["花柄が派手すぎない","花柄が上品","花柄の色数が抑えてある","花のサイズが大きすぎない"],
 "フローラル":["花柄が上品","柄が写真より落ち着いてる","花柄が甘くなりすぎない"],
 "ドット":["ドットの大きさがちょうどいい","ドット柄が可愛い","ドットが細かめで上品",
        "ドットの間隔がきれい"],
 "チェック":["チェックの色合いが落ち着いてる","チェックが派手じゃない","柄の出方がきれい",
         "チェックの大きさがちょうどいい","柄合わせが丁寧"],
 "ストライプ":["ストライプの幅がちょうどいい","縦のラインで細く見える","ストライプが上品"],
 "デニム":["デニムの色落ちがいい感じ","デニムが硬すぎない","生地はしっかりめのデニム",
        "デニムの色ムラが自然","洗ってもゴワつかなそう"],
 "サテン":["サテンの光沢が上品","チープな光り方じゃない","サテンがとろんとしてる","落ち感がきれい"],
 "ニット":["編み地がしっかりしてる","チクチクしない","編み目がきれい","ニットが柔らかい",
        "毛玉ができにくそう","伸びてよれる感じがない"],
 "透け":["透け感は控えめ","思ったより透けない","インナー次第で調整できる","透け方が上品"],
 "シアー":["シアー感が上品","透け方がきれい","重ねると雰囲気が出る"],
 "パフスリーブ":["パフ袖のふくらみが可愛い","肩まわりが華奢に見える","袖のボリュームが絶妙"],
 "オフショル":["肩の出方がちょうどいい","デコルテがきれいに見える","ずり落ちてこない"],
 "ギャザー":["ギャザーの寄せ方がきれい","ギャザーで体型を拾わない","ギャザーが自然"],
 "プリーツ":["プリーツがしっかりついてる","動くたびにきれい","プリーツが取れにくそう",
         "折り目がシャープ"],
 "スリット":["スリットは歩きやすい深さ","スリットが効いてる","スリットの位置がちょうどいい"],
 "刺繍":["刺繍が丁寧","刺繍のおかげで高見えする","刺繍の糸がほつれてない"],
 "ビジュー":["ビジューが上品に光る","装飾がチープじゃない","ビジューが取れそうにない"],
 "クロシェ":["クロシェ編みの質感が好き","手編み風で可愛い","編み目の抜け感がいい"],
 "メッシュ":["メッシュの目が細かい","透けすぎない","メッシュが涼しい"],
 "ハイウエスト":["ハイウエストで脚長効果すごい","腰位置が高く見える","ウエストの切り替えが高め"],
 "Aライン":["Aラインがきれいに出る","広がりすぎない","裾のフレアが上品"],
 "ホルターネック":["首まわりがすっきり","肩が出るぶん華奢に見える","紐で調整できる"],
 "カットアウト":["カットアウトの位置が絶妙","肌の見え方が上品","見えすぎない"],
 "リブ":["リブが伸びて着心地いい","フィット感が気持ちいい","リブがへたらなそう"],
 "ケーブル":["ケーブル編みが立体的","編み模様が可愛い","柄編みがきれい"],
 "コーデュロイ":["畝がきれい","秋冬っぽさが出る","コーデュロイの太さがちょうどいい"],
 "ツイード":["ツイードの織りが上品","高見えする","糸の色が複雑できれい"],
 "ベロア":["ベロアの起毛が上品","光沢がきれい","毛並みが揃ってる"],
 "チュール":["チュールの重なりが可愛い","ふわっと感がいい","チュールが硬すぎない"],
 "アシンメトリー":["左右非対称が効いてる","デザインが個性的","角度のつけ方が面白い"],
 "レトロ":["レトロな雰囲気が好み","古着っぽさがいい","今っぽさもある"],
 "ヴィンテージ":["ヴィンテージ感のある色味","くすみ加減が好き","こなれて見える"],
 "バンドゥ":["ずれにくい","安定感がある","ホールド感がしっかりしてる"],
 "ワッフル":["ワッフル地の凹凸が可愛い","肌ざわりがいい","生地に厚みがある"],
}
FITS = {
 "ゆったり":["ゆとりがあって楽","締めつけ感ゼロ","ゆるっと着られる","一日着てても疲れない"],
 "ルーズ":["ルーズで体型を拾わない","だぼっとしすぎない","抜け感がちょうどいい"],
 "オーバーサイズ":["大きめだけど着られてる感はない","ちょうどいい抜け感","肩の落ち方が自然"],
 "タイト":["タイトだけど窮屈じゃない","ラインがきれいに出る","伸びるので苦しくない"],
 "スリム":["体のラインがきれいに見える","すっきり見える","細見え効果あり"],
 "体型カバー":["気になるところを拾わない","体型カバー力ある","お腹まわりが安心"],
 "フィット":["ほどよくフィットする","きれいに沿う","変な浮きがない"],
}

GOOD = {
 "トップス":["一枚で決まる","合わせやすい","顔まわりが明るく見える","着回しが効く",
        "とりあえずこれ着とけば間違いない","洗い替えに欲しくなる","デイリーに使える"],
 "キャミソール":["インナーにも一枚でも使える","重ね着の幅が広がる","肩紐の位置がいい",
          "夏の主力になりそう","一枚あると便利","暑い日に助かる"],
 "スカート":["シルエットがきれい","丈感がちょうどいい","一枚で雰囲気が出る",
        "座ってもシワになりにくい","歩くとふわっとする","トップス選ばない"],
 "パンツ":["動きやすい","腰まわりが楽","カジュアルすぎず履ける","丈感がちょうどいい",
       "座っても苦しくない","毎日履きたくなる"],
 "ワンピース":["一枚で完成する","スタイルよく見える","シーンを選ばない",
         "考えなくていいのが楽","きちんと見える","着るだけで決まる"],
 "ニット":["長い期間着られそう","肌ざわりがいい","一枚で様になる","軽くて着やすい",
       "重ね着にも使える","家でも洗えそう"],
 "アウター":["羽織るだけで決まる","軽くて着やすい","中に着込める","肩がこらない",
       "室内でも暑くならない","持ち歩きやすい"],
 "セットアップ":["迷わず着られる","単品でも使える","統一感が出る","朝が楽になる",
          "旅行にも便利","セットで買う価値ある"],
 "水着":["気分が上がる","露出が高すぎない","羽織りと合わせやすい","乾きが早そう",
      "動いてもずれない","写真映えする"],
 "アイテム":["作りが丁寧","合わせやすい","雰囲気が出る","値段以上に見える","出番が多そう"],
}
STYLING = {
 "トップス":["デニムに合わせてます","スカートと合わせると女っぽくなる","羽織りとも相性いい",
        "パンツでもスカートでもいける","カーデを羽織って着てます","スニーカーでラフに"],
 "キャミソール":["シャツを羽織って抜け感","ハイウエストと合わせてます","カーデと重ねても可愛い",
          "Tシャツの上に重ねてます","ジャケットのインナーにも"],
 "スカート":["シンプルなトップスで十分","スニーカーでも綺麗めでもいける","タイツで秋冬も",
        "コンパクトなトップスと相性いい","ブーツと合わせるのが好き","白Tでいける"],
 "パンツ":["コンパクトなトップスと相性◎","スニーカーでラフに","ヒールで綺麗めに",
       "トップスインして履いてます","サンダルと合わせてます"],
 "ワンピース":["羽織りを足せば長く着られる","小物で印象が変わる","そのままで様になる",
         "ベルトでウエストマークしても可愛い","スニーカーで外して着てます"],
 "ニット":["ロングスカートと合わせるのが好き","インナー足して重ね着も","パンツでもスカートでも",
       "肩掛けでも使える","シャツの上から着てます"],
 "アウター":["中がシンプルでも決まる","丈短めのトップスと相性いい","色が落ち着いてて合わせやすい",
       "ワンピの上に羽織ってます","デニムと合わせるのが定番"],
 "セットアップ":["セットで着ると一気にまとまる","トップスだけでも使える","小物で印象が変わる",
          "ボトムスは他のトップスとも合う"],
 "水着":["羽織りとサンダルで街でもいける","上だけトップス代わりにも","小物で雰囲気変えてます",
      "パレオと合わせてます"],
 "アイテム":["手持ちとすぐ合わせられた","合わせるものを選ばない","小物で印象が変わる"],
}
SCENES = ["旅行用に買いました","デート用に","夏フェスで着ました","友達の結婚式の二次会に",
          "海行くとき用","普段使いに","写真撮るとき用に","ライブ用に買いました",
          "沖縄旅行に持っていきました","誕生日に自分へのご褒美で","子どもの行事用に",
          "推しのイベント用に","ディズニー行くとき用に","バイトの帰りに着替える用",
          "友達とごはん行くときに","撮影で使いました","文化祭で着ました","花火大会に着ていきました"]
CLOSERS_CASUAL = ["リピ確定","色違いも欲しい","買ってよかった","大満足","お気に入りになりました",
                  "また買います","めっちゃ気に入ってる","期待以上だった","もう何回も着てる",
                  "友達にも勧めた","即決してよかった","値段以上","当たりでした"]
CLOSERS_POLITE = ["買ってよかったです。","また利用します。","長く着られそうです。",
                  "期待どおりでした。","満足しています。","おすすめです。",
                  "リピートしたいと思います。","大事に着ます。","気に入りました。",
                  "また色違いも検討します。","良い買い物でした。"]
TITLES_CASUAL = ["可愛い","最高","好き","","神","買ってよかった","やばい可愛い","即リピ","優勝"]
TITLES_SIZE = ["サイズ感の参考に","サイズ表どおりでした","参考までに","サイズ迷ってる方へ",
               "身長別の参考に",""]
TITLES_MAT = ["生地がいい","思ったよりしっかりしてる","コスパ良し","","質感がいい",
              "値段のわりに丁寧"]
TITLES_STYLE = ["着回しやすい","コーデしやすい","","使いやすいです","毎日着てる"]
TITLES_EXP = ["写真より良い","イメージどおり","期待以上でした","","想像どおりでした"]
TITLES_SCENE = ["","旅行に持っていきました","出番多そう","買ってよかった","活躍しました"]
TITLES_REPEAT = ["リピートです","色違い購入","","二着目です"]
TITLES_GUSH = ["可愛すぎる","最高でした","ひと目惚れ","","テンション上がった"]
TITLES_DETAIL = ["お気に入り","参考になれば","","気に入ってます"]


def plain(body_html):
    return html.unescape(" ".join(re.sub(r"<[^>]+>", " ", body_html or "").split()))


def category(tags):
    t = set(tags)
    for name, keys in CATS:
        if t & set(keys):
            return name
    return "アイテム"


def parse_size_chart(body_html):
    text = unicodedata.normalize("NFKC", plain(body_html))
    m = re.search(r"サイズ((?:\s*(?:%s))+)(.*)$" % "|".join(SIZE_KEYS), text)
    if not m:
        return {}
    cols = re.findall("|".join(SIZE_KEYS), m.group(1))
    chart = {}
    pat = (r"(?<![A-Za-z])(XS|S|M|L|XL|XXL|2XL|3XL|F)(?![A-Za-z])"
           r"((?:\s*\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?)+)")
    for sm in re.finditer(pat, m.group(2)):
        cms = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*/", sm.group(2))]
        if cms:
            chart[sm.group(1)] = dict(zip(cols, cms))
    return chart


GARMENT = (r"(Dress|Coat|Vest|Top|Jacket|Skirt|Pants|Shirt|Set|Suit|Cardigan|Bottom|"
           r"ワンピース|コート|ベスト|トップス|ジャケット|スカート|パンツ|シャツ|セット|上|下)")
COLOR_JA = {"white":"ホワイト","black":"ブラック","green":"グリーン","red":"レッド",
            "brown":"ブラウン","blue":"ブルー","gray":"グレー","grey":"グレー",
            "apricot":"アプリコット","pink":"ピンク","dark blue":"ダークブルー",
            "khaki":"カーキ","beige":"ベージュ","coffee":"コーヒーブラウン",
            "burgundy":"バーガンディ","light yellow":"ライトイエロー","quiet black":"ブラック",
            "purple":"パープル","light gray":"ライトグレー","blue green":"ブルーグリーン",
            "dark brown":"ダークブラウン","navy":"ネイビー","coral pink":"コーラルピンク",
            "yellow":"イエロー","orange":"オレンジ","ivory":"アイボリー","mint":"ミント",
            "wine red":"ワインレッド","light blue":"ライトブルー","dark green":"ダークグリーン"}
NOT_COLOR = {"free","f","one size","onesize","default"}


def clean_color(c):
    c = re.sub(r"[（(].*?[)）]", "", c).strip()
    c = re.sub(r"\s*" + GARMENT + r"\s*$", "", c, flags=re.I).strip()
    c = re.sub(r"^\s*" + GARMENT + r"\s*", "", c, flags=re.I).strip()
    if not c or len(c) > 14 or re.search(GARMENT, c, re.I):
        return None
    if c.lower() in NOT_COLOR:
        return None
    return COLOR_JA.get(c.lower(), c)


def variant_axes(variants):
    colors, sizes = [], []
    for v in variants:
        for p in [x.strip() for x in (v.get("title") or "").split("/")]:
            if re.fullmatch(r"XS|S|M|L|XL|XXL|2XL|3XL|F|フリー", p):
                if p not in sizes:
                    sizes.append(p)
            elif p and p.lower() != "default title":
                c = clean_color(p)
                if c and c not in colors:
                    colors.append(c)
    return colors, sizes


class Ctx:
    """1商品ぶんの素材。型はここから必要なものだけ拾う。"""

    def __init__(self, prod, rng):
        self.rng = rng
        self.cat = category(prod.get("tags", []))
        self.chart = parse_size_chart(prod.get("body_html"))
        self.colors, self.sizes = variant_axes(prod.get("variants", []))
        blob = (prod["title"] + " " + plain(prod.get("body_html")).split("■")[0]
                + " " + " ".join(prod.get("tags", [])))
        self.feat_pool = [v for k, v in FEATURES.items() if k in blob]
        self.fit_pool = [v for k, v in FITS.items() if k in blob]
        try:
            self.price = int(float(prod["variants"][0]["price"]))
        except Exception:
            self.price = 0

    def size(self):
        return self.rng.choice(self.sizes) if self.sizes else "F"

    def height(self, size):
        lo, hi = SIZE_H.get(size, (150, 170))
        return self.rng.randrange(lo, hi + 1)

    def measures(self, size, n=2):
        row = self.chart.get(size, {})
        out = []
        for key in ("着丈", "ウエスト", "バスト", "胸囲", "総丈", "肩幅", "袖丈"):
            lo, hi = SANE.get(key, (0, 999))
            if key in row and lo <= row[key] <= hi:
                out.append("%s%gcm" % (key, row[key]))
            if len(out) >= n:
                break
        return out

    def feat(self):
        return self.rng.choice(self.rng.choice(self.feat_pool)) if self.feat_pool else None

    def fit(self):
        return self.rng.choice(self.rng.choice(self.fit_pool)) if self.fit_pool else None

    def color(self):
        return self.rng.choice(self.colors) if self.colors else None

    def good(self):
        return self.rng.choice(GOOD[self.cat])

    def styling(self):
        return self.rng.choice(STYLING[self.cat])


def emo(rng, pool, n=1):
    return "".join(rng.sample(pool, min(n, len(pool))))


# ---------------------------------------------------------------- 文体の型

def t_oneliner(c):
    r = c.rng
    bits = [c.feat() or c.good()]
    if r.random() < 0.6:
        bits.append(r.choice(CLOSERS_CASUAL))
    body = "、".join(bits) + r.choice(["！", "。", "〜！", "！！", "…！"])
    return r.choice(TITLES_CASUAL), body + emo(r, EMOJI_CUTE, r.randint(1, 3))


def t_size(c):
    r = c.rng
    s = c.size()
    ms = c.measures(s, 2)
    lines = [r.choice(["%dcm、普段%sサイズです。", "身長%dcmで普段は%sです。",
                       "%dcm・普段%s着用です。"]) % (c.height(s), s)]
    lines.append(("この商品も%sで、%sはほぼ表記どおりでした。" % (s, "・".join(ms))) if ms
                 else "%sでちょうどよかったです。" % s)
    f = c.fit()
    if f:
        lines.append(f + "。")
    lines.append(r.choice(["サイズ表どおりで選んで問題ないと思います。",
                           "迷ったら表記どおりで大丈夫だと思います。",
                           "普段のサイズで問題なかったです。",
                           "サイズ選びで悩む必要はなさそうです。"]))
    return r.choice(TITLES_SIZE), "".join(lines)


def t_material(c):
    r = c.rng
    bits = []
    f = c.feat()
    if f:
        bits.append(f)
    bits.append(r.choice(["生地がしっかりしていて安っぽくないです",
                          "縫製も雑なところがなかったです",
                          "薄すぎず、ちゃんとした作りでした",
                          "手に取った質感が値段以上でした",
                          "ペラペラじゃなくて安心しました",
                          "裏地までちゃんとしていました"]))
    if c.price:
        bits.append(r.choice(["この値段でこの質感なら十分満足です",
                              "%s円とは思えないです" % f"{c.price:,}",
                              "コスパは良いと思います",
                              "この価格帯だと当たりだと思います"]))
    return r.choice(TITLES_MAT), "。".join(bits) + "。"


def t_styling(c):
    r = c.rng
    bits = [c.styling(), c.good()]
    f = c.feat()
    if f:
        bits.insert(1, f)
    col = c.color()
    if col and r.random() < 0.55:
        bits.append(r.choice(["%sを選びましたが手持ちと合わせやすいです" % col,
                              "色は%sにしました" % col]))
    bits.append(r.choice(["出番が多くなりそうです", "着回しが効くので買ってよかったです",
                          "一枚あると便利だと思います", "手持ちで着回せそうです"]))
    body = "。".join(bits) + "。"
    return r.choice(TITLES_STYLE), body + (emo(r, EMOJI_PLAIN, 1) if r.random() < 0.35 else "")


def t_expect(c):
    r = c.rng
    bits = ["%s%s。" % (r.choice(["写真で見るより", "思っていたより", "届いてみたら",
                                  "画面で見るより", "レビューで見たとおり"]),
                        r.choice(["上品でした", "しっかりしてました", "落ち着いた色味でした",
                                  "可愛かったです", "きれいめに見えました", "しっかりした作りでした"]))]
    f = c.feat()
    if f:
        bits.append(f + "。")
    bits.append(c.good() + "。")
    if r.random() < 0.7:
        bits.append(c.styling() + "。")
    bits.append(r.choice(CLOSERS_POLITE))
    return r.choice(TITLES_EXP), "".join(bits)


def t_scene(c):
    r = c.rng
    bits = [r.choice(SCENES) + "。", c.good() + "。"]
    f = c.feat()
    if f:
        bits.append(f + "。")
    bits.append(c.styling() + "。")
    body = "".join(bits)
    return r.choice(TITLES_SCENE), body + (emo(r, EMOJI_CUTE, r.randint(1, 2)) if r.random() < 0.4 else "")


def t_bullets(c):
    r = c.rng
    plus = [x for x in [c.feat(), c.fit(), c.good(), c.styling()] if x]
    r.shuffle(plus)
    lines = ["◎ " + p for p in plus[:3]]
    if r.random() < 0.5:
        lines.append("△ " + r.choice(["少し透けるのでインナー必須",
                                      "色は画面より少し落ち着いてる",
                                      "シワになりやすいかも",
                                      "丈は短めなので好みが分かれそう",
                                      "届くまで少し時間がかかった",
                                      "タグが少しチクチクする"]))
    return r.choice(["まとめると", "良い点と気になる点", "", "箇条書きで"]), "\n".join(lines)


def t_repeat(c):
    r = c.rng
    col = c.color()
    bits = [r.choice(["二着目です", "色違いでリピしました", "前に買って良かったのでまた買いました",
                      "ここで買うの三回目です", "友達が着てて可愛かったので同じものを"]) + "。"]
    if col:
        bits.append("今回は%sにしました。" % col)
    bits.append(c.good() + "。")
    f = c.feat()
    if f:
        bits.append(f + "。")
    bits.append(r.choice(["やっぱり間違いないです。", "何回買っても満足してます。",
                          "またリピートすると思います。", "安定して良いです。"]))
    return r.choice(TITLES_REPEAT), "".join(bits)


def t_short_polite(c):
    r = c.rng
    bits = [c.good()]
    f = c.feat()
    if f:
        bits.append(f)
    fit = c.fit()
    if fit:
        bits.append(fit)
    return "", "。".join(bits) + "。" + r.choice(CLOSERS_POLITE)


def t_gush(c):
    r = c.rng
    bits = [r.choice(["届いた瞬間テンション上がりました", "写真どおりで感動", "可愛すぎる",
                      "ひと目惚れして買いました", "開けた瞬間に声出た", "想像の三倍可愛い"])]
    f = c.feat()
    if f:
        bits.append(f)
    bits.append(r.choice(CLOSERS_CASUAL))
    return r.choice(TITLES_GUSH), "、".join(bits) + "！" + emo(r, EMOJI_CUTE, r.randint(2, 3))


def t_detail(c):
    r = c.rng
    s = c.size()
    bits = []
    f = c.feat()
    if f:
        bits.append(f)
    bits.append("%dcmで%sを着用しています" % (c.height(s), s))
    fit = c.fit()
    if fit:
        bits.append(fit)
    bits.append(c.styling())
    bits.append(r.choice(CLOSERS_CASUAL))
    return r.choice(TITLES_DETAIL), "。".join(bits) + "。"


STYLES = [(t_oneliner, 14), (t_size, 11), (t_material, 12), (t_styling, 12),
          (t_expect, 11), (t_scene, 10), (t_bullets, 8), (t_repeat, 9),
          (t_short_polite, 8), (t_gush, 7), (t_detail, 10)]
FNS = [f for f, _ in STYLES]
WTS = [w for _, w in STYLES]


def pick_name(rng):
    pool = rng.choices([NAMES_KATA, NAMES_HIRA, NAMES_ROMA, NAMES_INIT],
                       weights=[52, 22, 13, 13])[0]
    name = rng.choice(pool)
    if pool is NAMES_KATA and rng.random() < 0.08:
        name += rng.choice(EMOJI_CUTE)
    return name


def main(src, out, per=2, seed=20260820, run_tag="b"):
    prods = json.load(open(src))
    start = date(2026, 3, 1)
    span = (date(2026, 8, 10) - start).days
    rows, seen = [], set()
    collisions = 0
    for p in prods:
        rng = random.Random("%d:%s" % (seed, p["handle"]))
        ctx = Ctx(p, rng)
        used_fn, used_name = set(), set()
        for i in range(per):
            title = body = None
            fn = None
            for attempt in range(UNIQUE_TRIES):
                cand_fn = rng.choices(FNS, weights=WTS)[0]
                if attempt < 20 and cand_fn in used_fn:
                    continue                       # 同一商品で型を重複させない
                t, b = cand_fn(ctx)
                if len(b) > MAX_LEN or b in seen:  # 長すぎ・既出は引き直す
                    collisions += 1
                    continue
                fn, title, body = cand_fn, t, b
                break
            if body is None:                       # 引き切れなかった場合の保険
                fn, title, body = cand_fn, t, b
            seen.add(body)
            used_fn.add(fn)
            for _ in range(20):
                name = pick_name(rng)
                if name not in used_name:
                    break
            used_name.add(name)
            d = start + timedelta(days=rng.randrange(span))
            rows.append({
                "title": title,
                "body": body,
                "rating": 5,
                "review_date": "%s %02d:%02d:%02d UTC" % (d.isoformat(), rng.randrange(24),
                                                          rng.randrange(60), rng.randrange(60)),
                "reviewer_name": name,
                # ハンドルは先頭が同じ商品同士でぶつかるため、一意な商品IDで作る。
                # run_tag は、投入をやり直すときに前回と同じ email が
                # Judge.me 側で重複扱いされるのを避けるためのもの。
                "reviewer_email": "p%s-%s%d@example.invalid" % (p["id"], run_tag, i + 1),
                "product_id": p["id"],
                "product_handle": p["handle"],
                "reply": "",
                "picture_urls": "",
            })
    cols = ["title", "body", "rating", "review_date", "reviewer_name", "reviewer_email",
            "product_id", "product_handle", "reply", "picture_urls"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    with open(out + ".NOTICE.txt", "w", encoding="utf-8") as f:
        f.write("このCSVのレビューは全て架空のテストデータです。\n"
                "実在の購入者・実注文には基づきません。\n\n"
                "パスワード保護されたストアでの表示確認専用です。\n"
                "保護を解除する場合は、解除前に Judge.me から全件削除してください。\n")
    dup = len(rows) - len({r["body"] for r in rows})
    print("products=%d reviews=%d 重複=%d 引き直し=%d -> %s"
          % (len(prods), len(rows), dup, collisions, out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2)
