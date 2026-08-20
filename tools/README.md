# tools/gen_reviews.py

VELA (vela-vela.com) の商品カタログから、Judge.me インポート用のレビューCSVを生成する。

## 生成されるデータについて

**このスクリプトが出力するレビューは全て架空である。** 実在の購入者・実注文には基づかない。
`verified_buyer=true` も実際の購入実績を表さない。

用途は、**パスワード保護されたストア**でのレビュー表示レイアウト確認に限る。

### 実行前の必須条件

ストアがパスワード保護されていること。次のコマンドで確認する。

```sh
curl -s https://vela-vela.com/ | grep -o '"onlineStorePasswordProtected":[a-z]*'
```

`true` でなければ実行しない。

### 保護を解除する場合

**解除前に、インポートした全レビューを Judge.me から削除すること。**
公開状態のストアに架空のレビューが残ると、購入者に対する誤認表示になる。
日本では景品表示法第5条第3号（2023年10月施行のいわゆるステマ規制）の対象となりうる。

## 使い方

```sh
# 1. カタログ取得（全ページ）
python3 fetch_catalog.py products_all.json

# 2. レビュー生成（1商品あたり2件）
python3 gen_reviews.py products_all.json reviews.csv 2
```

出力は Judge.me の Import 形式:
`product_handle, reviewer_name, reviewer_email, review_title, review_body, rating, review_date, verified_buyer, product_url`

## 生成ロジック

商品ごとに以下を読み取って本文を組み立てる。

- `body_html` のキャッチコピーから特徴語（レース、プリーツ、ホルターネックなど40種）を検出し、該当する言及文を挿入
- サイズ表を解析し、着用サイズの実寸（着丈・ウエスト・胸囲など）に言及。異常値は除外
- バリエーションから色名を抽出（`Black Dress` のような衣類名混じりは除去）
- 着用サイズと身長を相関させる（S=148-158cm, M=155-165cm, L=162-172cm）
- タグからカテゴリを判定し、カテゴリ別の着用感・着回し文を選択
- 同一商品内で投稿者名・タイトル・書き出しが重複しないようにする

`handle` をシードにするため、同じカタログからは常に同じ結果が出る。
