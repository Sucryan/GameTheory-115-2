#!/usr/bin/env bash
# 以 Pandoc + XeLaTeX 從 Markdown 產生 PDF（正確辨識 $...$ / $$...$$ 數學式）。
# Markdown PDF (yzane) 未內建數學外掛，$ 會當成一般字元；若要在 PDF 裡看到排版過的公式，請用此腳本。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/src/Report.md"
OUT="${1:-$ROOT/314581030_HW1_report.pdf}"

if [[ ! -f "$SRC" ]]; then
  echo "找不到來源檔：$SRC" >&2
  exit 1
fi

if ! command -v pandoc >/dev/null 2>&1; then
  echo "未安裝 pandoc。Ubuntu 範例：sudo apt install pandoc texlive-xetex texlive-lang-cjk texlive-fonts-recommended" >&2
  exit 1
fi

: "${CJK_FONT:=Noto Sans CJK TC}"

pandoc "$SRC" -o "$OUT" \
  --pdf-engine=xelatex \
  -V geometry:margin=2.5cm \
  -V CJKmainfont="${CJK_FONT}" \
  --highlight-style=tango

echo "已輸出：$OUT"
