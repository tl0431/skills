# md2pdf

A Claude Code skill that converts Markdown files into professionally styled PDFs. Pure Python, no browser required, full Chinese font support.

## Features

- 12 built-in themes (navy, forest, minimal, coral, and more)
- Auto-detects system fonts with bundled NotoSansSC as fallback
- Cover page, header/footer, auto-extracted document title
- Customizable styles via `pdf_style.yaml`
- Bilingual UI (Chinese/English)

## Usage

Just tell Claude Code what you want:

```
convert /path/to/notes.md to pdf, use the teal theme
generate a PDF from report.md with a cover page
md2pdf ~/Documents/proposal.md
把 report.md 转成 PDF，用 navy 主题
```

The skill will guide you through font and theme selection, then produce the PDF.

## File Structure

```
md2pdf/
├── SKILL.md                         # Skill entry point (read by Claude)
├── scripts/
│   ├── md2pdf.py                    # PDF generation script
│   └── font_finder.py               # System font scanner + yaml cache
├── assets/
│   └── fonts/
│       └── NotoSansSC-Regular.ttf   # Bundled CJK font (fallback)
└── references/
    └── style_schema.md              # pdf_style.yaml field reference
```

## Style Configuration

Create a `pdf_style.yaml` in your project directory to set defaults:

```yaml
default_font: PingFang SC    # auto-written after first selection
theme: navy                  # default theme

page_size: A4
margin_cm: 2.5

cover: true
cover_title: ""              # leave blank to auto-extract first H1

header: true
footer: true
```

See `references/style_schema.md` for the full field reference.

## Themes

| Theme | Style |
|-------|-------|
| navy | Dark blue, professional |
| forest | Deep green, natural |
| minimal | Clean black & white |
| warm | Warm brown, friendly |
| coral | Coral orange, energetic |
| slate | Slate gray, formal |
| purple | Purple, elegant |
| teal | Teal, fresh |
| gold | Gold, classic |
| rose | Rose pink, soft |
| midnight | Dark mode |
| olive | Olive green, understated |

## Requirements

```bash
pip install reportlab PyYAML
```

## Installation

Place this directory somewhere Claude Code can access it, or install from GitHub via the skill manager.

GitHub: https://github.com/tl0431/skills/tree/main/md2pdf
