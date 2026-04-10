---
name: md2pdf
description: Convert Markdown files to professionally styled PDFs. Use this skill when the user says: 把 md 转成 PDF、生成报告 PDF、md转pdf、md2pdf、convert markdown to PDF、generate PDF from markdown、export as PDF、把文章导出为 PDF、将 markdown 导出、生成 PDF 报告. Trigger even if the user doesn't say "skill" — any request to turn a .md file into a PDF should use this skill.
---

# md2pdf — Markdown to PDF Converter

## What this skill does

Converts a Markdown file to a professionally styled PDF using pure Python (ReportLab). No browser required. Full Chinese support. Configurable themes and fonts.

## Language behavior

All prompts are bilingual. Detect the language of the user's most recent message:
- Chinese last → Chinese first, English in parentheses: `请选择字体 / Please select a font:`
- English last → English first, Chinese in parentheses: `Please select a font / 请选择字体:`

## How to run this skill

### Step 1: Resolve input and output paths

Extract the input `.md` file path from the user's message. If relative, resolve to absolute using the current working directory.

Output path defaults to same directory, same name, `.pdf` extension. If the user specified a different output path, use that.

### Step 2: Font selection

Run: `python md2pdf/scripts/font_finder.py --yaml <path-to-pdf_style.yaml>`

This script:
1. Reads `pdf_style.yaml` `fonts` cache — if populated, skips glob scan
2. If no cache: scans system font directories, writes results to yaml
3. Returns JSON: `{"fonts": {"Name": "/path"}, "default_font": "Name or null"}`

If `default_font` is set in yaml → use it, skip prompt.

If not set → show font selection prompt (see format below), ask user to pick.
After user picks, ask: "设为默认字体？/ Set as default font? (y/n)"
- y → write `default_font` to yaml. If this is the FIRST time setting a default, show tip:
  > 已将 [字体名] 设为默认字体。如需修改，可在 `pdf_style.yaml` 中更改 `default_font` 字段，或在调用时说"这次用别的字体"临时覆盖。
  > Default font set to [font name]. To change it, edit `default_font` in `pdf_style.yaml`, or say "use a different font this time" to override temporarily.
- n → use for this session only

**Font selection prompt format:**
```
请选择字体 / Please select a font:
  1  PingFang SC
  2  Arial Unicode MS
  3  STHeiti
  ...
  0  其他 / Other (specify font name)
```

If user picks "Other" and the font is not found on system:
- Ask: "用途是商业还是非商业？/ Commercial or non-commercial use? (commercial/non-commercial)"
- non-commercial → use WebSearch to find a free download link, present top 3 options
- commercial → reply: "请自行购买字体授权并将字体文件放置到系统字体目录后重新运行。/ Please purchase a font license and place the font file in your system fonts directory, then re-run."

Final fallback (no font found at all): use bundled `md2pdf/assets/fonts/NotoSansSC-Regular.ttf`

### Step 3: Theme selection

Read `pdf_style.yaml` `theme` field.
- Set → use it, skip prompt
- Not set → show ANSI theme selector (see format in references/style_schema.md), ask user to pick
- After pick, ask: "设为默认主题？/ Set as default theme? (y/n)"
  - y → write `theme` to yaml
  - n → use for this session only

### Step 4: Run conversion

```bash
python md2pdf/scripts/md2pdf.py \
  --input "<input.md>" \
  --output "<output.pdf>" \
  --font "<font_path>" \
  --theme "<theme_name>" \
  --style "<pdf_style.yaml>"
```

### Step 5: Report result

Tell the user the output path and file size.
Example: `完成 / Done: report.pdf (245 KB)`
