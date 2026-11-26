# qsuke33の買ってよかったもの

実際に購入した商品のレビューサイトです。GitHub Pages（Jekyll）で <https://qsuke33.github.io> に公開します。

- 記事は `_posts/` に置くだけで、トップページの一覧に新しい順で自動表示されます。
- 全記事の冒頭に「広告・PR」、全ページのフッターに Amazon アソシエイトの表記が自動で入ります。
- 感想は自分のメモに書いたことだけを本文にします（スクリプトは文章を足したり作ったりしません）。

## アフィリエイトIDの設定（1か所だけ）

`_config.yml` の次の部分を書き換えて push するだけで、全記事の購入ボタンに反映されます。

```yaml
affiliate:
  amazon_tag: "xxxxx-22"                          # AmazonアソシエイトのトラッキングID
  rakuten_id: "xxxxxxxx.xxxxxxxx.xxxxxxxx.xxxxxxxx" # 楽天アフィリエイトID
```

空欄のままだと、IDなしの普通の商品リンクになります。
お問い合わせフォームを用意したら、同じファイルの `contact_form_url` にURLを入れてください。

## 記事の作り方（inbox の使い方）

### 1. inbox に商品ごとのフォルダを作る

```
inbox/
└── wireless-charger/      ← フォルダ名がそのまま記事のURLになる
    ├── memo.txt           ← 商品URLと感想
    ├── photo1.jpg         ← 写真（何枚でも）
    └── photo2.jpg
```

- フォルダ名は **半角英小文字・数字・ハイフン** だけ（例: `usb-charger`, `coffee-mill-2`）。
- 写真は JPG / PNG / WebP が使えます。iPhone の HEIC を使う場合は `pip install pillow-heif` が必要です
  （または iPhone の「設定 → カメラ → フォーマット → 互換性優先」で JPG にする）。
- 写真はファイル名の順に並びます。1枚目がトップ一覧のサムネイルになります。

### 2. memo.txt を書く

`inbox/_example/memo.txt` をコピーして使うのが簡単です。

```
タイトル: 〇〇を買って半年使った感想
商品名: 〇〇 ワイヤレス充電器 XYZ-100
カテゴリ: ガジェット
Amazon: https://www.amazon.co.jp/dp/B0XXXXXXXX
楽天: https://item.rakuten.co.jp/shop-name/item-code/
---
ここから下が感想。書いたとおりに記事本文になります。
```

| 項目 | 必須 | 説明 |
|---|---|---|
| タイトル | ○ | 記事のタイトル |
| 商品名 | | 記事冒頭と写真の説明に使う |
| カテゴリ | | 一覧と記事に表示 |
| Amazon | | 商品ページのURL。`/dp/` を含むURLならアソシエイトIDが自動で付きます（`amzn.asia` の短縮URLは不可） |
| 楽天 | | 楽天市場の商品ページのURL |

- `---` より下が感想（本文）です。**書いた文章がそのまま掲載されます。**
- Markdown が使えます（`## 見出し`、`- 箇条書き` など）。
- 写真を文中に入れたい位置に `[[photo1.jpg]]` と書けます。書かなかった写真は最後にまとめて載ります。

### 3. スクリプトを実行する

リポジトリのルートで:

```bash
pip install Pillow
python3 scripts/process_inbox.py
```

これで次の処理が行われます。

1. 写真から **位置情報（GPS）を含むメタデータ（EXIF）をすべて削除**（向きだけは画素に反映して保持）
2. 長辺 1200px に縮小して `assets/images/posts/<フォルダ名>/1.jpg, 2.jpg …` に保存
3. `_posts/<今日の日付>-<フォルダ名>.md` に記事を作成

- 一部だけ処理: `python3 scripts/process_inbox.py wireless-charger`
- 作り直し（メモを直したとき）: `python3 scripts/process_inbox.py --force wireless-charger`

### 4. 確認して公開

作られた `_posts/....md` を確認し、必要なら直接編集してから commit & push します。数分でサイトに反映されます。

```bash
git add _posts assets/images
git commit -m "記事追加: wireless-charger"
git push
```

> ⚠️ **inbox の中身は `.gitignore` でコミットされないようにしています。**
> 元の写真には撮影場所が入っていることがあるので、`git add -f` などで inbox の写真を無理に追加しないでください。
> 一度でも push すると、あとで消しても履歴に残ります。
> 同じ理由で、GitHub のWeb画面から inbox に写真を直接アップロードするのも避けてください。

## ファイル構成

| パス | 内容 |
|---|---|
| `_config.yml` | サイト名・アフィリエイトID・お問い合わせURL |
| `_posts/` | 記事（ここに置くと一覧に自動で出る） |
| `assets/images/posts/` | 公開用の写真（EXIF削除・縮小済み） |
| `_layouts/`, `_includes/` | ページの共通部分（広告・PR表示、購入ボタン、アソシエイト表記） |
| `assets/css/style.css` | デザイン |
| `profile.md`, `privacy.md`, `contact.md` | 固定ページ |
| `scripts/process_inbox.py` | inbox → 記事 の変換スクリプト |
| `inbox/` | 写真とメモの置き場（コミットされない） |

## ローカルでプレビュー（任意）

```bash
bundle install
bundle exec jekyll serve
```

ブラウザで <http://localhost:4000> を開きます。
