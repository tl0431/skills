---
name: md2pdf
description: ALWAYS use this skill when the user wants to convert a Markdown (.md) file into a PDF. Triggers: md2pdf, .md file + PDF output, 把 .md 转成 PDF, 导出为 PDF, export .md as pdf, generate PDF from markdown, 生成 PDF, 打印成 PDF, nicely formatted pdf, convert markdown to pdf, turn .md into pdf, 将 markdown 导出为 PDF. If the user mentions any .md file and wants a PDF — use this skill. Do NOT use for: reading PDFs, Word/CSV/webpage→PDF, MD→HTML, MD→PPT, or translating/formatting markdown.
---

# md2pdf — Markdown to PDF Converter

## What this skill does

Converts a Markdown file to a professionally styled PDF using pure Python (ReportLab). No browser required. Full Chinese support. Configurable themes and fonts.

## Language behavior

All prompts are bilingual. Detect the language of the user's most recent message:
- Chinese last → Chinese first, English in parentheses: `请选择字体 / Please select a font:`
- English last → English first, Chinese in parentheses: `Please select a font / 请选择字体:`

## How to run this skill

### Step 0: Check for updates (silent, non-blocking)

Run the following command. If it prints an update notice, show it to the user before continuing. If it produces no output or fails, skip silently.

```bash
python3 -c "
import urllib.request, ssl, os
try:
    vfile = '<skills_dir>/VERSION'
    local = open(vfile).read().strip() if os.path.exists(vfile) else None
    ctx = ssl._create_unverified_context()
    remote = urllib.request.urlopen(
        'https://raw.githubusercontent.com/tl0431/skills/main/VERSION',
        timeout=2, context=ctx
    ).read().decode().strip()
    if local is None:
        print(f'⚠️  md2pdf: VERSION file not found. Latest is v{remote}.')
        print(f'   Run to update: cd <skills_dir> && git pull')
    elif local != remote:
        print(f'⚠️  md2pdf update available: v{local} → v{remote}')
        print(f'   Run to update: cd <skills_dir> && git pull')
except:
    pass
" 2>/dev/null
```

### Step 1: Resolve input and output paths

Extract the input `.md` file path from the user's message. If relative, resolve to absolute using the current working directory.

Output path defaults to same directory, same name, `.pdf` extension. If the user specified a different output path, use that.

### Step 1.5: Quick or Custom mode

Ask the user:

```
模式 / Mode:
  1  快速 / Quick   — GitHub 风格，立即生成（推荐）
  2  自定义 / Custom — 选择字体、主题、封面

选择 (1/2, 直接回车 = 1 / press Enter = 1):
```

**If user chooses 1 (Quick / default):**
- Font: use `default_font` from `pdf_style.yaml` if set; otherwise use bundled `NotoSansSC-Regular.ttf`
- Theme: `github`
- Skip Steps 2, 3, 3.5 entirely
- Run Step 4 with `--theme github --no-cover` and no `--style` flag (or use yaml only if it exists)
- Report result per Step 5

**If user chooses 2 (Custom):**
- Continue with Steps 2 → 3 → 3.5 → 4 as normal

### Step 2: Font selection

Run: `python md2pdf/scripts/font_finder.py --yaml <path-to-pdf_style.yaml>`

The yaml path is `<user-cwd>/pdf_style.yaml` — the user's current working directory, NOT the skill directory.

This script:
1. Reads `pdf_style.yaml` `fonts` cache — if populated, skips glob scan
2. If no cache: scans system font directories, tests ReportLab compatibility, writes results to yaml
3. Returns JSON: `{"fonts": {"Name": {"path": "/...", "format": "TTF"}}, "default_font": "Name or null"}`

**All fonts returned are guaranteed ReportLab-compatible** (tested at scan time).

If `default_font` is set in yaml → use it, skip prompt.

If not set → show font selection prompt (see format below), ask user to pick.
After user picks, ask: "设为默认字体？/ Set as default font? (y/n)"
- y → write `default_font` to yaml. If this is the FIRST time setting a default, show tip:
  > 已将 [字体名] 设为默认字体。如需修改，可在 `pdf_style.yaml` 中更改 `default_font` 字段，或在调用时说"这次用别的字体"临时覆盖。
  > Default font set to [font name]. To change it, edit `default_font` in `pdf_style.yaml`, or say "use a different font this time" to override temporarily.
- n → use for this session only

**Font selection prompt format** — use box-drawing style, one font per row:
```
请选择字体 / Please select a font:
  ┌───┬──────────────────────┬───────┐
  │ 1 │ Arial Unicode        │ [TTF] │
  │ 2 │ Hiragino Sans GB     │ [TTF] │
  │ 3 │ NotoSansSC (bundled) │ [TTF] │
  │ 4 │ STHeiti Light        │ [TTC] │
  │ 0 │ 其他 / Other         │       │
  └───┴──────────────────────┴───────┘
```

Font path is `fonts[selected_name]["path"]`.

If user picks "Other" and the font is not found on system:
- Ask: "用途是商业还是非商业？/ Commercial or non-commercial use? (commercial/non-commercial)"
- non-commercial → use WebSearch to find a free download link, present top 3 options
- commercial → reply: "请自行购买字体授权并将字体文件放置到系统字体目录后重新运行。/ Please purchase a font license and place the font file in your system fonts directory, then re-run."

Final fallback (no font found at all): use bundled `md2pdf/assets/fonts/NotoSansSC-Regular.ttf`

### Step 3: Theme selection

Read `pdf_style.yaml` `theme` field.
- Set → use it, skip prompt
- Not set → run the following Bash command to display the color selector, then ask user to pick:

```bash
python <skills_dir>/scripts/md2pdf.py --print-themes
```

(Replace `<skills_dir>` with the absolute path to the md2pdf skill directory, e.g. `/Users/username/.claude/skills/md2pdf`)

**Valid theme names:** navy, minimal, warm, slate, gold, midnight, custom

If user enters an invalid name, run the command again and ask to re-pick.

- After pick, ask: "设为默认主题？/ Set as default theme? (y/n)"
  - y → write `theme` to yaml
  - n → use for this session only

### Step 3.5: Cover page configuration

Ask: "是否生成封面页？/ Include a cover page? (y/n)"

- **n** → pass `--no-cover` flag (Step 4). Skip all cover prompts below.
- **y** → ask the following two prompts (Enter = use default, no further input needed):
  - "封面标题 / Cover title: (直接回车 = 文档第一个 H1 / press Enter = first H1)"
    - If user presses Enter (empty input) → do NOT write `cover_title` to yaml (let converter use H1 default)
    - If user types a title → write to `pdf_style.yaml` as `cover_title`
  - "副标题 / Subtitle: (直接回车跳过 / press Enter to skip)"
    - If user presses Enter → do NOT write `cover_subtitle`
    - If user types → write to `pdf_style.yaml` as `cover_subtitle`
  - Do NOT ask about meta separately. Auto-write today's date as default:
    Write `cover_meta` to `pdf_style.yaml` with value: current date in format `YYYY年M月`

### Step 4: Run conversion

```bash
python md2pdf/scripts/md2pdf.py \
  --input "<input.md>" \
  --output "<output.pdf>" \
  --font "<font_path>" \
  --theme "<theme_name>" \
  --style "<pdf_style.yaml>" \
  [--no-cover]
```

Add `--no-cover` if user said no to cover page in Step 3.5.

### Step 5: Report result

Tell the user the output path and file size.
Example: `完成 / Done: report.pdf (245 KB)`
