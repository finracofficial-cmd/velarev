# -*- coding: utf-8 -*-
"""VELA / Judge.me インポート用ダミーレビュー生成器。

出力データは全て架空。実在の購入者・実注文には基づかない。
パスワード保護下のストアでの表示確認用。

文体を1つの型に固定すると、何件並べても同じ文章に見える。そのため
複数の型（短文・サイズ重視・素材重視・箇条書き など）を用意し、商品ごとに
別の型を割り当てる。身長や着用サイズに言及するのは一部の型だけ。
"""
import csv, html, json, random, re, sys, unicodedata
from datetime import date, timedelta

# ---------------------------------------------------------------- 投稿者名
# 表記もばらけさせる（カタカナ / ひらがな / 英字 / イニシャル）
NAMES_KATA = ["ハルカ","ミナ","リオ","アオイ","ユナ","ナナ","サキ","カレン","モモ","ヒナ",
              "マリン","アカリ","ノア","セナ","ミオ","ユイ","ソラ","コハル","リコ","マナ",
              "アヤ","チヒロ","ナギサ","スミレ","ホノカ","ルナ","エマ","シオリ","カナ","ミク"]
NAMES_HIRA = ["はるか","みな","ゆい","あおい","なな","もも","ひなの","さき","りん","ここ",
              "まな","あかり","ちひろ","すみれ","ゆきの","みお"]
NAMES_ROMA = ["Yui","Mina","Aoi","Nana","Rio","Sena","Karen","Momo","Haruka","Luna"]
NAMES_INIT = ["M.K","Y.S","A.T","R.N","K","N.H","S.Y","mii","non","ちー"]

EMOJI_CUTE = ["🎀","🥺","💕","🩷","✨","🫶","😍","☺️","🌸","💗"]
EMOJI_PLAIN = ["👍","😊","🙆‍♀️","✨","👗","🫧"]

# ---------------------------------------------------------------- 商品カテゴリ
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

# 特徴語 -> 複数の言い回し。同じ特徴でも商品ごとに違う文になる。
FEATURES = {
 "レース":["レースが上品","レースの透け感が絶妙","レースが安っぽくない","レース部分がとにかく可愛い"],
 "フリル":["フリルの量がちょうどいい","フリルが甘すぎない","フリルにボリュームがある"],
 "リボン":["リボンが主役","リボンの位置が絶妙","リボンが取り外せたらもっと良かったけど可愛い"],
 "花柄":["花柄が派手すぎない","花柄が上品","花柄の色数が抑えてある"],
 "フローラル":["花柄が上品","柄が写真より落ち着いてる"],
 "ドット":["ドットの大きさがちょうどいい","ドット柄が可愛い","ドットが細かめで上品"],
 "チェック":["チェックの色合いが落ち着いてる","チェックが派手じゃない","柄の出方がきれい"],
 "ストライプ":["ストライプの幅がちょうどいい","縦のラインで細く見える"],
 "デニム":["デニムの色落ちがいい感じ","デニムが硬すぎない","生地はしっかりめのデニム"],
 "サテン":["サテンの光沢が上品","チープな光り方じゃない","サテンがとろんとしてる"],
 "ニット":["編み地がしっかりしてる","チクチクしない","編み目がきれい","ニットが柔らかい"],
 "透け":["透け感は控えめ","思ったより透けない","インナー次第で調整できる"],
 "シアー":["シアー感が上品","透け方がきれい"],
 "パフスリーブ":["パフ袖のふくらみが可愛い","肩まわりが華奢に見える"],
 "オフショル":["肩の出方がちょうどいい","デコルテがきれいに見える"],
 "ギャザー":["ギャザーの寄せ方がきれい","ギャザーで体型を拾わない"],
 "プリーツ":["プリーツがしっかりついてる","動くたびにきれい","プリーツが取れにくそう"],
 "スリット":["スリットは歩きやすい深さ","スリットが効いてる"],
 "刺繍":["刺繍が丁寧","刺繍のおかげで高見えする"],
 "ビジュー":["ビジューが上品に光る","装飾がチープじゃない"],
 "クロシェ":["クロシェ編みの質感が好き","手編み風で可愛い"],
 "メッシュ":["メッシュの目が細かい","透けすぎない"],
 "ハイウエスト":["ハイウエストで脚長効果すごい","腰位置が高く見える"],
 "Aライン":["Aラインがきれいに出る","広がりすぎない"],
 "ホルターネック":["首まわりがすっきり","肩が出るぶん華奢に見える"],
 "カットアウト":["カットアウトの位置が絶妙","肌の見え方が上品"],
 "リブ":["リブが伸びて着心地いい","フィット感が気持ちいい"],
 "ケーブル":["ケーブル編みが立体的","編み模様が可愛い"],
 "コーデュロイ":["畝がきれい","秋冬っぽさが出る"],
 "ツイード":["ツイードの織りが上品","高見えする"],
 "ベロア":["ベロアの起毛が上品","光沢がきれい"],
 "チュール":["チュールの重なりが可愛い","ふわっと感がいい"],
 "アシンメトリー":["左右非対称が効いてる","デザインが個性的"],
 "レトロ":["レトロな雰囲気が好み","古着っぽさがいい"],
 "ヴィンテージ":["ヴィンテージ感のある色味","くすみ加減が好き"],
 "バンドゥ":["ずれにくい","安定感がある"],
 "ワッフル":["ワッフル地の凹凸が可愛い","肌ざわりがいい"],
}
FITS = {
 "ゆったり":["ゆとりがあって楽","締めつけ感ゼロ","ゆるっと着られる"],
 "ルーズ":["ルーズで体型を拾わない","だぼっとしすぎない"],
 "オーバーサイズ":["大きめだけど着られてる感はない","ちょうどいい抜け感"],
 "タイト":["タイトだけど窮屈じゃない","ラインがきれいに出る"],
 "スリム":["体のラインがきれいに見える","すっきり見える"],
 "体型カバー":["気になるところを拾わない","体型カバー力ある"],
 "フィット":["ほどよくフィットする","きれいに沿う"],
}

# カテゴリ別の一言（型によって使い分ける）
GOOD = {
 "トップス":["一枚で決まる","合わせやすい","顔まわりが明るく見える","着回しが効く"],
 "キャミソール":["インナーにも一枚でも使える","重ね着の幅が広がる","肩紐の位置がいい"],
 "スカート":["シルエットがきれい","丈感がちょうどいい","一枚で雰囲気が出る"],
 "パンツ":["動きやすい","腰まわりが楽","カジュアルすぎず履ける"],
 "ワンピース":["一枚で完成する","スタイルよく見える","シーンを選ばない"],
 "ニット":["長い期間着られそう","肌ざわりがいい","一枚で様になる"],
 "アウター":["羽織るだけで決まる","軽くて着やすい","中に着込める"],
 "セットアップ":["迷わず着られる","単品でも使える","統一感が出る"],
 "水着":["気分が上がる","露出が高すぎない","羽織りと合わせやすい"],
 "アイテム":["作りが丁寧","合わせやすい","雰囲気が出る"],
}
STYLING = {
 "トップス":["デニムに合わせてます","スカートと合わせると女っぽくなる","羽織りとも相性いい"],
 "キャミソール":["シャツを羽織って抜け感","ハイウエストと合わせてます","カーデと重ねても可愛い"],
 "スカート":["シンプルなトップスで十分","スニーカーでも綺麗めでもいける","タイツで秋冬も"],
 "パンツ":["コンパクトなトップスと相性◎","スニーカーでラフに","ヒールで綺麗めに"],
 "ワンピース":["羽織りを足せば長く着られる","小物で印象が変わる","そのままで様になる"],
 "ニット":["ロングスカートと合わせるのが好き","インナー足して重ね着も","パンツでもスカートでも"],
 "アウター":["中がシンプルでも決まる","丈短めのトップスと相性いい","色が落ち着いてて合わせやすい"],
 "セットアップ":["セットで着ると一気にまとまる","トップスだけでも使える","小物で印象が変わる"],
 "水着":["羽織りとサンダルで街でもいける","上だけトップス代わりにも","小物で雰囲気変えてます"],
 "アイテム":["手持ちとすぐ合わせられた","合わせるものを選ばない","小物で印象が変わる"],
}
SCENES = ["旅行用に買いました","デート用に","夏フェスで着ました","友達の結婚式の二次会に",
          "海行くとき用","普段使いに","写真撮るとき用に","ライブ用に買いました"]
CLOSERS_CASUAL = ["リピ確定","色違いも欲しい","買ってよかった","大満足","お気に入りになりました",
                  "また買います","めっちゃ気に入ってる"]
CLOSERS_POLITE = ["買ってよかったです。","また利用します。","長く着られそうです。",
                  "期待どおりでした。","満足しています。","おすすめです。"]


def plain(body_html):
    t = re.sub(r"<[^>]+>", " ", body_html or "")
    return html.unescape(" ".join(t.split()))


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
    pat = r"(?<![A-Za-z])(XS|S|M|L|XL|XXL|2XL|3XL|F)(?![A-Za-z])((?:\s*\d+(?:\.\d+)?\s*/\s*\d+(?:\.\d+)?)+)"
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
    key = c.lower()
    if key in NOT_COLOR:
        return None
    return COLOR_JA.get(key, c)


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
        self.feats = [rng.choice(v) for k, v in FEATURES.items() if k in blob]
        self.fits = [rng.choice(v) for k, v in FITS.items() if k in blob]
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
            if key in row and SANE.get(key, (0, 999))[0] <= row[key] <= SANE.get(key, (0, 999))[1]:
                out.append("%s%gcm" % (key, row[key]))
            if len(out) >= n:
                break
        return out

    def feat(self):
        return self.rng.choice(self.feats) if self.feats else None

    def fit(self):
        return self.rng.choice(self.fits) if self.fits else None

    def color(self):
        return self.rng.choice(self.colors) if self.colors else None

    def good(self):
        return self.rng.choice(GOOD[self.cat])

    def styling(self):
        return self.rng.choice(STYLING[self.cat])


def emo(rng, pool, n=1):
    return "".join(rng.sample(pool, min(n, len(pool))))


# ---------------------------------------------------------------- 文体の型
# 各型は (title, body) を返す。身長・サイズに触れるのは一部だけ。

def t_oneliner(c):
    """短文・カジュアル。絵文字あり。サイズ言及なし。"""
    r = c.rng
    bits = [c.feat() or c.good()]
    if r.random() < 0.5:
        bits.append(r.choice(CLOSERS_CASUAL))
    body = "、".join(bits) + r.choice(["！", "。", "〜！", "！！"])
    body += emo(r, EMOJI_CUTE, r.randint(1, 3))
    return r.choice(["可愛い", "最高", "好き", "", "神", "買ってよかった"]), body


def t_size(c):
    """サイズ・実寸重視。絵文字なし、敬体。"""
    r = c.rng
    s = c.size()
    h = c.height(s)
    ms = c.measures(s, 2)
    lines = ["%dcm、普段%sサイズです。" % (h, s)]
    if ms:
        lines.append("この商品も%sで、%sはほぼ表記どおりでした。" % (s, "・".join(ms)))
    else:
        lines.append("%sでちょうどよかったです。" % s)
    f = c.fit()
    if f:
        lines.append(f + "。")
    lines.append(r.choice(["サイズ表どおりで選んで問題ないと思います。",
                           "迷ったら表記どおりで大丈夫だと思います。",
                           "普段のサイズで問題なかったです。"]))
    if r.random() < 0.6:
        lines.append(c.styling() + "。")
    return r.choice(["サイズ感の参考に", "サイズ表どおりでした", "参考までに", "サイズ迷ってる方へ"]), "".join(lines)


def t_material(c):
    """素材・質感と価格対比。"""
    r = c.rng
    bits = []
    f = c.feat()
    if f:
        bits.append(f)
    bits.append(r.choice(["生地がしっかりしていて安っぽくないです",
                          "縫製も雑なところがなかったです",
                          "薄すぎず、ちゃんとした作りでした",
                          "手に取った質感が値段以上でした"]))
    if c.price:
        bits.append(r.choice(["この値段でこの質感なら十分満足です",
                              "%s円とは思えないです" % f"{c.price:,}",
                              "コスパは良いと思います"]))
    return r.choice(["生地がいい", "思ったよりしっかりしてる", "コスパ良し", ""]), "。".join(bits) + "。"


def t_styling(c):
    """着回し中心。サイズ言及なし。"""
    r = c.rng
    bits = [c.styling(), c.good()]
    f = c.feat()
    if f:
        bits.insert(1, f)
    col = c.color()
    if col and r.random() < 0.6:
        bits.append("%sを選びましたが手持ちと合わせやすいです" % col)
    bits.append(r.choice(["出番が多くなりそうです", "着回しが効くので買ってよかったです",
                          "一枚あると便利だと思います"]))
    body = "。".join(bits) + "。"
    if r.random() < 0.35:
        body += emo(r, EMOJI_PLAIN, 1)
    return r.choice(["着回しやすい", "コーデしやすい", "", "使いやすいです"]), body


def t_expect(c):
    """期待との比較。"""
    r = c.rng
    lead = r.choice(["写真で見るより", "思っていたより", "届いてみたら", "画面で見るより"])
    tail = r.choice(["上品でした", "しっかりしてました", "落ち着いた色味でした",
                     "可愛かったです", "きれいめに見えました"])
    bits = ["%s%s。" % (lead, tail)]
    f = c.feat()
    if f:
        bits.append(f + "。")
    bits.append(c.good() + "。")
    if r.random() < 0.7:
        bits.append(c.styling() + "。")
    bits.append(r.choice(CLOSERS_POLITE))
    return r.choice(["写真より良い", "イメージどおり", "期待以上でした", ""]), "".join(bits)


def t_scene(c):
    """用途・シーン。"""
    r = c.rng
    bits = [r.choice(SCENES) + "。", c.good() + "。"]
    f = c.feat()
    if f:
        bits.append(f + "。")
    bits.append(c.styling() + "。")
    if r.random() < 0.5:
        bits.append(r.choice(CLOSERS_POLITE))
    body = "".join(bits)
    if r.random() < 0.4:
        body += emo(r, EMOJI_CUTE, r.randint(1, 2))
    return r.choice(["", "旅行に持っていきました", "出番多そう", "買ってよかった"]), body


def t_bullets(c):
    """箇条書き風。"""
    r = c.rng
    plus = [x for x in [c.feat(), c.fit(), c.good()] if x]
    r.shuffle(plus)
    lines = ["◎ " + p for p in plus[:3]]
    if r.random() < 0.45:
        lines.append("△ " + r.choice(["少し透けるのでインナー必須",
                                      "色は画面より少し落ち着いてる",
                                      "シワになりやすいかも",
                                      "丈は短めなので好みが分かれそう"]))
    return r.choice(["まとめると", "良い点と気になる点", ""]), "\n".join(lines)


def t_repeat(c):
    """リピーター視点。"""
    r = c.rng
    col = c.color()
    bits = [r.choice(["二着目です", "色違いでリピしました", "前に買って良かったのでまた買いました",
                      "ここで買うの三回目です"]) + "。"]
    if col:
        bits.append("今回は%sにしました。" % col)
    bits.append(c.good() + "。")
    f = c.feat()
    if f:
        bits.append(f + "。")
    bits.append(r.choice(["やっぱり間違いないです。", "何回買っても満足してます。",
                          "またリピートすると思います。"]))
    body = "".join(bits)
    if r.random() < 0.4:
        body += emo(r, EMOJI_PLAIN, 1)
    return r.choice(["リピートです", "色違い購入", ""]), body


def t_short_polite(c):
    """淡々と短く敬体。絵文字なし。"""
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
    """テンション高め、絵文字多め。"""
    r = c.rng
    bits = [r.choice(["届いた瞬間テンション上がりました", "写真どおりで感動", "可愛すぎる",
                      "ひと目惚れして買いました"])]
    f = c.feat()
    if f:
        bits.append(f)
    bits.append(r.choice(CLOSERS_CASUAL))
    return r.choice(["可愛すぎる", "最高でした", "ひと目惚れ"]), \
        "、".join(bits) + "！" + emo(r, EMOJI_CUTE, r.randint(2, 3))


def t_detail(c):
    """やや長め。サイズにも触れる総合型。"""
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
    return r.choice(["お気に入り", "詳しめに書きます", "参考になれば", ""]), "。".join(bits) + "。"


def t_long(c):
    """長文。購入動機から着用感まで書く型。数は少なめ。"""
    r = c.rng
    sz = c.size()
    bits = []
    bits.append(r.choice([
        "前から似たようなものを探していて、写真の雰囲気に惹かれて購入しました。",
        "セールになっていたので思いきって買ってみました。",
        "レビューが少なくて少し迷ったのですが、思いきって注文しました。",
        "同系統のものを持っていないので、試しに買ってみました。"]))
    f = c.feat() or "作りが丁寧"
    bits.append(r.choice([
        "届いて袋から出してまず思ったのが、%s ということ。" % f,
        "実物を手に取ってみると、%s。" % f,
        "写真では分かりませんでしたが、%s。" % f]))
    ms = c.measures(sz, 2)
    if ms:
        bits.append("%dcmで%sを着用していて、%sは表記とほぼ同じでした。" % (c.height(sz), sz, "・".join(ms)))
    else:
        bits.append("%dcmで%sを選んでちょうどよかったです。" % (c.height(sz), sz))
    fit = c.fit()
    if fit:
        bits.append("%s。長時間着ていても疲れませんでした。" % fit)
    bits.append(c.styling() + "。")
    if r.random() < 0.5:
        bits.append(r.choice([
            "強いて言えば、色は画面で見るより少し落ち着いて見えます。",
            "気になった点は、届いたときの折りジワが少し取れにくかったことくらいです。",
            "洗濯は念のためネットに入れています。"]))
    bits.append(r.choice(CLOSERS_POLITE))
    return r.choice(["長くなりましたが", "購入を迷っている方へ", "詳しく書きます", ""]), "".join(bits)


# (関数, 重み)。サイズ言及があるのは t_size / t_detail / t_long のみ。
STYLES = [(t_oneliner, 14), (t_size, 10), (t_material, 11), (t_styling, 12),
          (t_expect, 11), (t_scene, 9), (t_bullets, 7), (t_repeat, 8),
          (t_short_polite, 8), (t_gush, 6), (t_detail, 10), (t_long, 6)]


def pick_name(rng):
    pool = rng.choices([NAMES_KATA, NAMES_HIRA, NAMES_ROMA, NAMES_INIT],
                       weights=[55, 20, 13, 12])[0]
    name = rng.choice(pool)
    if pool is NAMES_KATA and rng.random() < 0.08:
        name += rng.choice(EMOJI_CUTE)
    return name


def main(src, out, per=2, seed=20260820):
    prods = json.load(open(src))
    start = date(2026, 3, 1)
    span = (date(2026, 8, 10) - start).days
    rows = []
    for p in prods:
        rng = random.Random("%d:%s" % (seed, p["handle"]))
        ctx = Ctx(p, rng)
        fns = [f for f, _ in STYLES]
        wts = [w for _, w in STYLES]
        used_fn, used_name = set(), set()
        for i in range(per):
            for _ in range(12):                       # 同一商品で型と名前を重複させない
                fn = rng.choices(fns, weights=wts)[0]
                name = pick_name(rng)
                if fn not in used_fn and name not in used_name:
                    break
            used_fn.add(fn)
            used_name.add(name)
            title, body = fn(ctx)
            d = start + timedelta(days=rng.randrange(span))
            stamp = "%s %02d:%02d:%02d UTC" % (d.isoformat(), rng.randrange(24),
                                               rng.randrange(60), rng.randrange(60))
            rows.append({
                "title": title,
                "body": body,
                "rating": 5,
                "review_date": stamp,
                "reviewer_name": name,
                "reviewer_email": "%s-%d@example.invalid" % (p["handle"][:24], i + 1),
                "product_id": p["id"],
                "product_handle": p["handle"],
                "reply": "",
                "picture_urls": "",
            })
    cols = ["title", "body", "rating", "review_date", "reviewer_name", "reviewer_email",
            "product_id", "product_handle", "reply", "picture_urls"]
    with open(out, "w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=cols).writeheader()
        csv.DictWriter(f, fieldnames=cols).writerows(rows)
    with open(out + ".NOTICE.txt", "w", encoding="utf-8") as f:
        f.write("このCSVのレビューは全て架空のテストデータです。\n"
                "実在の購入者・実注文には基づきません。\n\n"
                "パスワード保護されたストアでの表示確認専用です。\n"
                "保護を解除する場合は、解除前に Judge.me から全件削除してください。\n")
    print("products=%d reviews=%d -> %s" % (len(prods), len(rows), out))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 2)
