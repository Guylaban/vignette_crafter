# drawio sources

Editable sources for the diagrams used in the paper at [`6863a6dda45292b7b830a08c/`](../../6863a6dda45292b7b830a08c/).

## Files

| File | Sheets |
|---|---|
| `cohort_icons.drawio` | `multi-agent` (1), `gitflow` (2), `CTF game flow` (3), `Single-Agent` (4), `model` (5) |
| `cohort_conversation.drawio` | `Page-1` (1) |

> ⚠️ drawio-desktop's `--page-index` is **1-indexed** despite the name. Page 1 is the first sheet, not page 0.

Indices are in file order. Verify with:

```bash
grep -oE '<diagram[^>]*name="[^"]*"' cohort_icons.drawio
```

## Editing

Open in the [drawio web app](https://app.diagrams.net/) (File → Open) or the desktop app. Commit the `.drawio` file after editing — do not commit exported PDFs/PNGs in this folder; exports live under [`../../6863a6dda45292b7b830a08c/Content/Images/`](../../6863a6dda45292b7b830a08c/Content/Images/).

## Exporting to the paper

Use drawio's native PDF export. drawio-desktop renders via headless Chromium, which handles the `<foreignObject>` elements drawio uses for text and complex icons — and embeds (subsets) whatever fonts are installed locally. Do **not** route through Inkscape: it drops `foreignObject` content silently, so labels and many icons disappear.

### One-time setup (headless Ubuntu VM)

```bash
# drawio-desktop
URL=$(curl -s https://api.github.com/repos/jgraph/drawio-desktop/releases/latest \
  | grep -oE '"browser_download_url": "[^"]*drawio-amd64-[^"]*\.deb"' \
  | cut -d'"' -f4)
curl -L -o /tmp/drawio.deb "$URL"
sudo apt install -y /tmp/drawio.deb xvfb fonts-liberation poppler-utils
```

- `xvfb` — drawio-desktop is an Electron app and needs a display server even in CLI mode.
- `fonts-liberation` — metric-equivalent substitutes for Helvetica/Arial.
- `poppler-utils` — provides `pdffonts` for verifying embedded fonts after export.

### Fonts

drawio's PDF export uses Chromium, which embeds (subsets) whatever fonts it finds locally. If a font referenced in the diagram isn't installed, fontconfig picks an unrelated fallback (e.g. Helvetica → Liberation Serif) and the PDF looks wrong.

Our diagrams use **Comic Sans MS**. Install the real Microsoft fonts — free to redistribute for personal use, requires accepting the EULA non-interactively:

```bash
echo ttf-mscorefonts-installer msttcorefonts/accepted-mscorefonts-eula select true \
  | sudo debconf-set-selections
sudo apt install -y ttf-mscorefonts-installer
fc-cache -f
```

Verify with `fc-match "Comic Sans MS"` — it should report `Comic_Sans_MS.ttf`, not a fallback.

After exporting, inspect the PDF to confirm the right fonts were embedded:

```bash
pdffonts multi-agent.pdf
# Look for ComicSansMS / ComicSansMS-Bold with emb=yes, sub=yes
```

If a diagram uses a different font, install its package (or add a fontconfig alias in `~/.config/fontconfig/fonts.conf`) and re-export.

### Export one sheet

Pick a sheet by name — the output PDF is named after the sheet.

```bash
cd docs/drawio

SRC=cohort_icons.drawio
SHEET="multi-agent"
OUT_DIR=../../6863a6dda45292b7b830a08c/Content/Images

IDX=$(grep -oE '<diagram[^>]*name="[^"]*"' "$SRC" \
      | grep -n "name=\"$SHEET\"" | head -1 | cut -d: -f1)

xvfb-run -a drawio --no-sandbox --export --format pdf --crop \
  --page-index "$IDX" \
  --output "$OUT_DIR/$SHEET.pdf" "$SRC"
```

Flags that matter:
- `--crop` — trim whitespace around the diagram
- `--no-sandbox` — required because Chromium's sandbox can't initialize under Xvfb on this VM

You can ignore the `dbus … systemd1.UnitExists` warning — it's Chromium complaining about sandboxing under Xvfb.

### Batch export everything the paper uses

```bash
cd docs/drawio
OUT=../../6863a6dda45292b7b830a08c/Content/diagrams/Images

export_sheet() {
  local src=$1 idx=$2 name=$3
  xvfb-run -a drawio --no-sandbox --export --format pdf --crop \
    --page-index "$idx" \
    --output "$OUT/$name.pdf" "$src"
}

export_sheet cohort_icons.drawio 1 multi-agent
export_sheet cohort_icons.drawio 2 gitflow
export_sheet cohort_icons.drawio 4 Single-Agent
export_sheet cohort_icons.drawio 5 model
```

### Exporting as PNG

Same flow, swap `--format pdf` for `--format png` and add raster-specific flags:

- `--scale 4` — 4× resolution. PNG is raster, so pick based on use: ~2 for web, 4+ for print.
- `--transparent` — transparent background. Omit for white.

Export one sheet:

```bash
cd docs/drawio

SRC=cohort_icons.drawio
SHEET="multi-agent"
OUT=../../6863a6dda45292b7b830a08c/Content/diagrams/Images

IDX=$(grep -oE '<diagram[^>]*name="[^"]*"' "$SRC" \
      | grep -n "name=\"$SHEET\"" | head -1 | cut -d: -f1)

xvfb-run -a drawio --no-sandbox --export --format png --crop \
  --scale 4 --transparent \
  --page-index "$IDX" \
  --output "$OUT_DIR/$SHEET.png" "$SRC"
```

Batch export:

```bash
cd docs/drawio
OUT=../../6863a6dda45292b7b830a08c/Content/Images

export_sheet_png() {
  local src=$1 idx=$2 name=$3
  xvfb-run -a drawio --no-sandbox --export --format png --crop \
    --scale 4 --transparent \
    --page-index "$idx" \
    --output "$OUT/$name.png" "$src"
}

export_sheet_png cohort_icons.drawio 1 multi-agent
export_sheet_png cohort_icons.drawio 2 gitflow
export_sheet_png cohort_icons.drawio 4 Single-Agent
export_sheet_png cohort_icons.drawio 5 model
```

## Including in LaTeX

`graphicx` is already loaded in [`preamble.tex`](../../6863a6dda45292b7b830a08c/preamble.tex); use PDFs like any other figure:

```latex
\includegraphics[width=0.95\linewidth]{Content/Images/multi-agent.pdf}
```
