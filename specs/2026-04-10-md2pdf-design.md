# md2pdf Skill — Design Spec

**Date:** 2026-04-10  
**Status:** Draft

---

## Overview

A Claude Code skill that converts Markdown files to professionally styled PDFs. Pure Python, no browser dependency, fast (seconds), full Chinese support. Designed to be shareable across users and platforms.

Replaces the existing `gen_pdf_chrome.js` (Puppeteer/browser-based, slow) and the project-specific `gen_pdf.py` (hardcoded paths and styles).

---

## Skill Structure

```
md2pdf/
├── SKILL.md                        # Skill entry point, trigger logic, usage instructions
├── scripts/
│   ├── md2pdf.py                   # Main conversion script (also runnable as standalone CLI)
│   └── font_finder.py              # Font scanning, caching, and selection logic
├── assets/
│   └── fonts/
│       └── NotoSansSC-Regular.ttf  # Bundled fallback font (Apache 2.0, open source)
└── references/
    └── style_schema.md             # pdf_style.yaml field documentation
```

---

## Trigger Conditions

The skill activates on both Chinese and English phrases, including but not limited to:

- 把 X.md 转成 PDF / 生成报告 PDF / md转pdf / md2pdf
- convert markdown to PDF / generate PDF from markdown / export as PDF

---

## Language Behavior

All user-facing prompts and messages are bilingual (Chinese + English). The language order and emphasis adapts to the user's most recent message:
- If the user's last message was in Chinese → Chinese first, English in parentheses
- If the user's last message was in English → English first, Chinese in parentheses

Example:
> 请选择字体 / Please select a font:
> Please select a font / 请选择字体:

This applies to: font selection prompts, theme selection prompts, default-setting confirmations, error messages, and all other interactive output.

---

## Technology Stack

- **PDF rendering:** ReportLab (pure Python, no system dependencies)
- **Font:** User system fonts (auto-detected) with bundled NotoSansSC as fallback
- **Configuration:** `pdf_style.yaml` in the working directory
- **Font scanning:** Python `glob` module for recursive filesystem search

---

## Font Selection Flow

Font selection runs once per invocation unless a default is already set.

```
1. Read pdf_style.yaml `fonts` mapping (cache)
   └─ Cache exists → skip glob scan
   └─ No cache → glob scan system font directories → write results to yaml cache

2. Check pdf_style.yaml `default_font`
   └─ Set → use it directly, skip user prompt
   └─ Not set → show font selection prompt (list found Chinese fonts)

3. User selects font from list
   └─ "Set as default?" prompt
       └─ Yes → write `default_font` to yaml + show modification tip (first time only)
       └─ No → use for this session only

4. User requests a font not found in system
   └─ Ask: commercial or non-commercial use?
       └─ Non-commercial → WebSearch for free download link, present options
       └─ Commercial → prompt user to purchase license and place font file manually

5. Final fallback → bundled NotoSansSC-Regular.ttf
```

**System font scan paths:**

| Platform | Paths |
|----------|-------|
| macOS | `/Library/Fonts/**`, `~/Library/Fonts/**`, `/System/Library/Fonts/**` |
| Windows | `C:\Windows\Fonts\**` |
| Linux | `/usr/share/fonts/**`, `~/.fonts/**`, `/usr/local/share/fonts/**` |

Scan uses `glob` with `*.ttf`, `*.otf`, `*.ttc` patterns. Results filtered by Chinese font name keywords: Arial Unicode, PingFang, YaHei, SimSun, SimHei, STHeiti, Hiragino, Noto CJK, Source Han, WenQuanYi.

**First-time default font tip (shown once):**
> "已将 [字体名] 设为默认字体。如需修改，可以在 `pdf_style.yaml` 中更改 `default_font` 字段，或在调用时说'这次用别的字体'临时覆盖。"

---

## Theme Selection Flow

```
1. Read pdf_style.yaml `theme`
   └─ Set → use it directly, skip prompt
   └─ Not set → show ANSI color block theme selector

2. User selects theme
   └─ "Set as default?" prompt
       └─ Yes → write `theme` to yaml
       └─ No → use for this session only
```

**ANSI color block display format:**

```
请选择主题 / Select theme:
  1  ██████  Navy        深海军蓝，专业商务
  2  ██████  Forest      深绿，学术自然
  3  ██████  Minimal     黑白极简
  4  ██████  Warm        暖棕，人文学术
  5  ██████  Coral       珊瑚红，活力现代
  6  ██████  Slate       石板灰，低调稳重
  7  ██████  Purple      深紫，科技感
  8  ██████  Teal        青绿，清新简洁
  9  ██████  Gold        金棕，高端商务
 10  ██████  Rose        玫瑰粉，轻奢优雅
 11  ██████  Midnight    午夜黑，极简暗色
 12  ██████  Olive       橄榄绿，自然沉稳
  0  自定义 / Custom（输入 hex 颜色值）
```

Each `██████` block is rendered using ANSI background color codes approximating the theme's accent color.

**Built-in theme color values:**

| Theme | Accent | Dark | Muted |
|-------|--------|------|-------|
| navy | #1C3A5E | #1A1A2E | #888888 |
| forest | #2D5A27 | #1A2E1A | #888888 |
| minimal | #333333 | #111111 | #999999 |
| warm | #7B4F2E | #2E1A0E | #999999 |
| coral | #C0392B | #2C1810 | #888888 |
| slate | #4A5568 | #1A202C | #888888 |
| purple | #553C9A | #1A0E2E | #888888 |
| teal | #2C7A7B | #0E2E2E | #888888 |
| gold | #B7791F | #2E1E0E | #888888 |
| rose | #B83280 | #2E0E1E | #888888 |
| midnight | #2D3748 | #0A0A0A | #999999 |
| olive | #556B2F | #1A2010 | #888888 |

---

## `pdf_style.yaml` Schema

```yaml
# Font cache (auto-populated by font_finder.py, do not edit manually)
fonts:
  PingFang SC: /System/Library/Fonts/PingFang.ttc
  Arial Unicode: /Library/Fonts/Arial Unicode.ttf
default_font: PingFang SC

# Theme
theme: navy   # See theme list above; use 'custom' to specify hex values below
# Only used when theme: custom
custom_accent: "#1C3A5E"
custom_dark: "#1A1A2E"
custom_muted: "#888888"

# Page layout
page_size: A4       # A4 or Letter
margin_cm: 2.5      # Applied to all four sides

# Cover page
cover: true
cover_title: ""     # Defaults to first H1 in the markdown
cover_subtitle: ""
cover_meta: ""      # e.g. date, author, classification

# Header & footer (content auto-extracted from document)
header: true
footer: true
footer_page_number: true
```

---

## Markdown Rendering Support

Supports the following markdown elements (based on existing `gen_pdf.py` parser):

| Element | Rendered As |
|---------|-------------|
| `# H1` | Large heading + horizontal rule |
| `## H2` | Medium heading |
| `### H3` | Small heading |
| Body text | Justified paragraph |
| `- item` / `* item` | Bullet list |
| `1. item` | Numbered list |
| `> quote` | Callout block with left accent border |
| ` ```code``` ` | Code block with monospace font |
| `---` | Horizontal rule |
| `\| table \|` | Styled table with header row |
| `**bold**` / `*italic*` / `` `inline` `` | Inline formatting |

---

## Input / Output

- **Input:** Any `.md` file path (absolute or relative)
- **Output:** Same directory, same filename with `.pdf` extension (default)
- **Override:** User can specify a different output path in the prompt (e.g., "save to ~/Desktop/report.pdf")

---

## Standalone CLI Usage

`md2pdf.py` is also runnable directly without Claude:

```bash
python md2pdf.py input.md [output.pdf] [--style pdf_style.yaml]
```

---

## Out of Scope (v1)

- Images in markdown
- Custom CSS
- Table of contents generation
- Multi-column layouts
- Background images on cover
- Logo on cover
