#!/usr/bin/env python3
"""inbox/ の写真とメモから記事を作るスクリプト。

使い方（リポジトリのルートで実行）:
    pip install Pillow            # 初回のみ（iPhoneのHEICも使うなら pillow-heif も）
    python3 scripts/process_inbox.py            # inbox 内の未処理フォルダをすべて処理
    python3 scripts/process_inbox.py my-item    # 指定したフォルダだけ処理
    python3 scripts/process_inbox.py --force my-item   # 既存の記事・写真を上書き

やること:
  1. inbox/<フォルダ名>/ の写真から位置情報などのメタデータ(EXIF)を完全に消す
  2. 長辺 MAX_SIZE px に縮小して JPEG で assets/images/posts/<フォルダ名>/ に保存
  3. memo.txt の内容から _posts/<日付>-<フォルダ名>.md を作る
     感想はメモに書いた文章をそのまま本文にする（文章を足したり作ったりしない）
"""
import argparse
import datetime as dt
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps
except ImportError:
    sys.exit("Pillow が必要です: pip install Pillow")

try:  # iPhone の HEIC 写真用（任意）
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIC_OK = True
except ImportError:
    HEIC_OK = False

ROOT = Path(__file__).resolve().parent.parent
INBOX = ROOT / "inbox"
POSTS = ROOT / "_posts"
IMAGES = ROOT / "assets" / "images" / "posts"

MAX_SIZE = 1200      # 長辺の最大ピクセル
JPEG_QUALITY = 80
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
JST = dt.timezone(dt.timedelta(hours=9))

KEYS = {
    "タイトル": "title", "title": "title",
    "商品名": "product", "product": "product",
    "カテゴリ": "category", "category": "category",
    "amazon": "amazon", "アマゾン": "amazon",
    "楽天": "rakuten", "rakuten": "rakuten",
}


def parse_memo(text):
    """'キー: 値' のヘッダーと、'---' 以降の感想本文に分ける。"""
    head, sep, body = text.partition("\n---")
    if not sep:
        sys.exit("memo.txt に区切り線 '---' がありません（_example/memo.txt を参照）")
    meta = {}
    for line in head.splitlines():
        m = re.match(r"^\s*([^:：]+)[:：]\s*(.*)$", line)
        if m:
            key = KEYS.get(m.group(1).strip().lower())
            if key and m.group(2).strip():
                meta[key] = m.group(2).strip()
    body = body.split("\n", 1)[1] if "\n" in body else ""
    return meta, body.strip()


def amazon_asin(url):
    m = re.search(r"/(?:dp|gp/product|gp/aw/d|exec/obidos/ASIN)/([A-Z0-9]{10})", url)
    return m.group(1) if m else None


def clean_rakuten(url):
    # 自分の過去のアフィリエイトリンクなどが貼られていても、そのまま使う
    return url.split("#")[0]


def process_photo(src, dst):
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)  # 回転情報を画素に反映してから EXIF を捨てる
        if im.mode not in ("RGB", "L"):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            rgba = im.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[-1])
            im = bg
        im.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
        # 画素だけを新しい画像にコピー → EXIF/GPS/XMP/コメント等を一切持ち越さない
        clean = Image.frombytes(im.mode, im.size, im.tobytes())
    dst.parent.mkdir(parents=True, exist_ok=True)
    clean.save(dst, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    # 念のため検証
    with Image.open(dst) as check:
        if check.getexif() or "exif" in check.info or "xmp" in check.info:
            dst.unlink()
            sys.exit(f"メタデータが残ったため中止しました: {src}")


def yaml_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def process_folder(folder, force=False):
    slug = folder.name
    if not SLUG_RE.match(slug):
        print(f"× {slug}: フォルダ名は半角英小文字・数字・ハイフンにしてください（例: usb-charger）")
        return False
    memo = folder / "memo.txt"
    if not memo.exists():
        print(f"× {slug}: memo.txt がありません")
        return False

    existing = list(POSTS.glob(f"*-{slug}.md"))
    if existing and not force:
        print(f"- {slug}: 記事 {existing[0].name} が既にあるのでスキップ（上書きは --force）")
        return False

    meta, body = parse_memo(memo.read_text(encoding="utf-8"))
    if "title" not in meta:
        print(f"× {slug}: memo.txt に「タイトル:」がありません")
        return False
    if not body:
        print(f"× {slug}: 感想（--- より下）が空です")
        return False

    photos = sorted(p for p in folder.iterdir() if p.suffix.lower() in PHOTO_EXT)
    if any(p.suffix.lower() in {".heic", ".heif"} for p in photos) and not HEIC_OK:
        print(f"× {slug}: HEIC 写真には pip install pillow-heif が必要です")
        return False

    out_dir = IMAGES / slug
    if force and out_dir.exists():
        for old in out_dir.glob("*.jpg"):
            old.unlink()
    urls = {}
    for i, p in enumerate(photos, 1):
        dst = out_dir / f"{i}.jpg"
        process_photo(p, dst)
        urls[p.name] = f"/assets/images/posts/{slug}/{i}.jpg"
        print(f"  写真 {p.name} → {dst.relative_to(ROOT)}（EXIF削除・縮小済み）")

    alt = meta.get("product", meta["title"])
    used = set()

    def place(m):
        name = m.group(1).strip()
        if name in urls:
            used.add(name)
            return f"![{alt}]({urls[name]})"
        print(f"  ! 本文の [[{name}]] に対応する写真がありません")
        return m.group(0)

    # 本文中の [[ファイル名]] を写真に置き換え。指定のない写真は末尾にまとめる
    body = re.sub(r"\[\[([^\]]+)\]\]", place, body)
    rest = [n for n in urls if n not in used]
    if rest:
        body += "\n\n## 写真\n\n" + "\n\n".join(f"![{alt}]({urls[n]})" for n in rest)

    now = dt.datetime.now(JST)
    fm = ["---", f"title: {yaml_str(meta['title'])}",
          f"date: {now.strftime('%Y-%m-%d %H:%M:%S +0900')}"]
    if "product" in meta:
        fm.append(f"product: {yaml_str(meta['product'])}")
    if "category" in meta:
        fm.append(f"category: {yaml_str(meta['category'])}")
    if urls:
        fm.append(f"image: {urls[photos[0].name]}")
    if "amazon" in meta:
        asin = amazon_asin(meta["amazon"])
        fm.append(f"amazon_asin: {asin}" if asin else f"amazon_url: {yaml_str(meta['amazon'])}")
        if not asin:
            print("  ! AmazonのURLから商品コード(ASIN)を読み取れませんでした。"
                  "amazon.co.jp/dp/XXXXXXXXXX 形式のURLにするとアソシエイトIDが自動で付きます")
    if "rakuten" in meta:
        fm.append(f"rakuten_url: {yaml_str(clean_rakuten(meta['rakuten']))}")
    fm.append("---")

    for old in existing:
        old.unlink()
    POSTS.mkdir(exist_ok=True)
    post = POSTS / f"{now.strftime('%Y-%m-%d')}-{slug}.md"
    post.write_text("\n".join(fm) + "\n\n" + body + "\n", encoding="utf-8")
    print(f"○ {slug}: 記事を作成 → {post.relative_to(ROOT)}")
    return True


def main():
    ap = argparse.ArgumentParser(description="inbox の写真とメモから記事を作る")
    ap.add_argument("folders", nargs="*", help="処理するフォルダ名（省略時はすべて）")
    ap.add_argument("--force", action="store_true", help="既存の記事・写真を上書き")
    args = ap.parse_args()

    if args.folders:
        targets = [INBOX / f for f in args.folders]
    else:
        targets = sorted(p for p in INBOX.iterdir()
                         if p.is_dir() and not p.name.startswith(("_", ".")))
    if not targets:
        print("inbox に処理するフォルダがありません")
        return
    for t in targets:
        if not t.is_dir():
            print(f"× {t.name}: inbox/{t.name} が見つかりません")
            continue
        process_folder(t, force=args.force)


if __name__ == "__main__":
    main()
