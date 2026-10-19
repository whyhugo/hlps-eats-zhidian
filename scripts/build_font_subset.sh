#!/usr/bin/env bash
# 重新產生網頁標題字型子集（Noto Serif TC Black，SIL OFL）。
# 菜單新增了新字、或網頁改了標題文字後執行：bash scripts/build_font_subset.sh
set -euo pipefail
cd "$(dirname "$0")/.."
TMP=$(mktemp -d)
curl -sSL -o "$TMP/NotoSerifTC-Black.otf" "https://github.com/notofonts/noto-cjk/raw/main/Serif/SubsetOTF/TC/NotoSerifTC-Black.otf"
cat web/*.html web/*.js data/processed/dishes.csv config/*.json src/fitwell/*.py > "$TMP/chars.txt"
printf '%s' '０１２３４５６７８９一二三四五六七八九十上中下籤宜食適量少吃空盤「」！—·・、，。：？（）ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789' >> "$TMP/chars.txt"
uvx --from 'fonttools[woff]' pyftsubset "$TMP/NotoSerifTC-Black.otf" --text-file="$TMP/chars.txt" \
  --flavor=woff2 --layout-features='*' --output-file=web/fonts/NotoSerifTC-Black-subset.woff2
rm -rf "$TMP"
echo "已更新 web/fonts/NotoSerifTC-Black-subset.woff2"
