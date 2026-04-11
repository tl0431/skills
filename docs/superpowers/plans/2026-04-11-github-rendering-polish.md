# GitHub Rendering Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the github theme visually match GitHub's markdown preview as closely as possible within ReportLab's constraints, covering 7 specific rendering improvements.

**Architecture:** All changes are in `scripts/md2pdf.py`. Tasks are independent and additive: parser improvements (task list, table alignment), style improvements (inline code color, code block bg+font, blockquote left bar, heading sizes), and font improvements (monospace for code). Each change is backward-compatible — non-github themes are unaffected except where noted.

**Tech Stack:** Python 3, ReportLab, pytest.

---

## File Map

| File | Change |
|------|--------|
| `scripts/md2pdf.py` | All 7 improvements |
| `scripts/test_md2pdf.py` | New tests per task (TDD) |
| `~/.claude/skills/md2pdf/scripts/md2pdf.py` | Sync at end |
| `~/.claude/skills/md2pdf/scripts/test_md2pdf.py` | Sync at end |

All edits in `/Users/TL_1/Desktop/工作/工作/md2pdf/scripts/`. Sync to `~/.claude/skills/md2pdf/scripts/` only at the end.

---
## Task 1: Inline code color (`#0550ae` for github theme)

**GitHub behavior:** `` `code` `` renders with blue text `#0550ae` and a subtle `rgba(175,184,193,0.2)` background. ReportLab XML `<font>` tags don't support background mid-paragraph, so we implement: (a) blue text color via new `code_color` theme key, (b) `backColor` on `code_inline` ParagraphStyle for standalone code paragraphs.

**Files:**
- Modify: `scripts/md2pdf.py` — `THEMES` dict, `resolve_theme()`, `build_styles()`
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 1.1: Write failing tests**

Add to `scripts/test_md2pdf.py` after `test_build_styles_h1_uses_heading_color`:

```python
def test_github_theme_has_code_color():
    """github theme must have code_color key (blue for inline code)."""
    c = md2pdf.resolve_theme("github", {})
    assert "code_color" in c
    # GitHub inline code is #0550ae — blue channel dominant
    assert c["code_color"].blue > 0.5
    assert c["code_color"].red < 0.3


def test_build_styles_code_inline_uses_code_color():
    """code_inline style must use theme code_color for github theme."""
    md2pdf.register_font(BUNDLED_FONT, "CodeColorFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("CodeColorFont", colors_github)
    assert styles["code_inline"].textColor == colors_github["code_color"]


def test_existing_themes_code_color_equals_dark():
    """Non-github themes: code_color must equal dark (backward compat)."""
    for name in ["navy", "minimal", "warm"]:
        c = md2pdf.resolve_theme(name, {})
        assert c["code_color"].hexval() == c["dark"].hexval(), \
            f"{name}: code_color should equal dark"
```

- [ ] **Step 1.2: Run tests to confirm RED**

```bash
cd /Users/TL_1/Desktop/工作/工作/md2pdf
python -m pytest scripts/test_md2pdf.py::test_github_theme_has_code_color scripts/test_md2pdf.py::test_build_styles_code_inline_uses_code_color scripts/test_md2pdf.py::test_existing_themes_code_color_equals_dark -v 2>&1 | tail -15
```

Expected: all 3 FAIL.

- [ ] **Step 1.3: Add `code_color` to github THEMES entry**

In `scripts/md2pdf.py`, update the github entry:

```python
    "github":   {"accent": "#0366d6", "dark": "#24292e", "muted": "#6a737d",
                 "heading_color": "#24292e", "separator_color": "#eaecef",
                 "table_header_bg": "#f6f8fa", "table_header_fg": "#24292e",
                 "code_color": "#0550ae"},
```

- [ ] **Step 1.4: Extend `resolve_theme` to return `code_color`**

In `resolve_theme`, in the `else` branch add after `table_header_fg` line:
```python
        code_color      = t.get("code_color",      dark)
```

In the `custom` branch add:
```python
        code_color = dark
```

Update the return dict to include:
```python
        "code_color":      hex_to_color(code_color),
```

- [ ] **Step 1.5: Update `build_styles` — `code_inline` uses `code_color` + backColor**

Replace the `code_inline` entry in `build_styles`:

```python
        "code_inline": ParagraphStyle("code_inline", fontSize=10, spaceAfter=4,
                                      fontName=font_name,
                                      textColor=theme_colors["code_color"],
                                      backColor=colors.Color(0.965, 0.973, 0.980),
                                      leading=16),
```

- [ ] **Step 1.6: Run full suite**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 64 tests pass (61 + 3 new).

- [ ] **Step 1.7: Commit**

```bash
cd /Users/TL_1/Desktop/工作/工作
git add md2pdf/scripts/md2pdf.py md2pdf/scripts/test_md2pdf.py
git commit -m "feat: add code_color theme key and inline code background"
```

---
## Task 2: Code block — `#f6f8fa` background + monospace font

**GitHub behavior:** Code blocks use `#f6f8fa` background and `SFMono-Regular`/`Consolas`/`Menlo` monospace font.

**Current behavior:** `rgb(0.95,0.95,0.95)` background, same font as body text.

**Approach:** Add `code_bg` theme key. Add `find_mono_font()` that checks system paths for Menlo/Consolas/Courier New. Add `mono_font_name` optional param to `build_styles`. Wire into `convert()`.

**Files:**
- Modify: `scripts/md2pdf.py` — `THEMES`, `resolve_theme()`, `build_styles()`, `convert()`
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 2.1: Write failing tests**

Add to `scripts/test_md2pdf.py`:

```python
def test_github_code_block_background_is_f6f8fa():
    """code_block backColor for github theme must be #f6f8fa (all channels > 0.96)."""
    md2pdf.register_font(BUNDLED_FONT, "CodeBgFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("CodeBgFont", colors_github)
    bg = styles["code_block"].backColor
    assert bg.red > 0.96 and bg.green > 0.96 and bg.blue > 0.96, \
        f"Expected #f6f8fa-ish background, got {bg}"


def test_build_styles_code_block_uses_mono_font():
    """code_block and code_inline must use mono_font_name when provided."""
    md2pdf.register_font(BUNDLED_FONT, "BodyFont2")
    md2pdf.register_font(BUNDLED_FONT, "MonoFont2")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("BodyFont2", colors_github, mono_font_name="MonoFont2")
    assert styles["code_block"].fontName == "MonoFont2"
    assert styles["code_inline"].fontName == "MonoFont2"
```

- [ ] **Step 2.2: Run tests to confirm RED**

```bash
python -m pytest scripts/test_md2pdf.py::test_github_code_block_background_is_f6f8fa scripts/test_md2pdf.py::test_build_styles_code_block_uses_mono_font -v 2>&1 | tail -15
```

Expected: both FAIL.

- [ ] **Step 2.3: Add `code_bg` to github THEMES entry**

```python
    "github":   {"accent": "#0366d6", "dark": "#24292e", "muted": "#6a737d",
                 "heading_color": "#24292e", "separator_color": "#eaecef",
                 "table_header_bg": "#f6f8fa", "table_header_fg": "#24292e",
                 "code_color": "#0550ae", "code_bg": "#f6f8fa"},
```

- [ ] **Step 2.4: Extend `resolve_theme` to return `code_bg`**

In `else` branch add: `code_bg = t.get("code_bg", "#f0f0f0")`
In `custom` branch add: `code_bg = "#f0f0f0"`
Return dict: `"code_bg": hex_to_color(code_bg),`

- [ ] **Step 2.5: Add `find_mono_font()` after `register_font` function**

```python
_MONO_CANDIDATES = [
    "/System/Library/Fonts/Menlo.ttc",
    "/Library/Fonts/Courier New.ttf",
    "C:/Windows/Fonts/consola.ttf",
    "C:/Windows/Fonts/cour.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

def find_mono_font() -> str | None:
    """Return path to first available monospace font, or None."""
    for p in _MONO_CANDIDATES:
        if Path(p).exists():
            return p
    return None
```

- [ ] **Step 2.6: Update `build_styles` signature and code styles**

Change signature:
```python
def build_styles(font_name: str, theme_colors: dict,
                 mono_font_name: str = None) -> dict:
```

Add after `heading = theme_colors["heading_color"]`:
```python
    _mono = mono_font_name or font_name
```

Update `code_inline` and `code_block` entries:
```python
        "code_inline": ParagraphStyle("code_inline", fontSize=10, spaceAfter=4,
                                      fontName=_mono,
                                      textColor=theme_colors["code_color"],
                                      backColor=colors.Color(0.965, 0.973, 0.980),
                                      leading=16),
        "code_block": ParagraphStyle("code_block", fontSize=9, spaceAfter=8,
                                     spaceBefore=4, fontName=_mono,
                                     textColor=dark, leading=14,
                                     leftIndent=12,
                                     backColor=theme_colors["code_bg"]),
```

- [ ] **Step 2.7: Wire `find_mono_font()` into `convert()`**

In `convert()`, find the line `styles = build_styles(font_name, theme_colors)` and replace with:

```python
    mono_font_name = font_name
    mono_path = find_mono_font()
    if mono_path:
        try:
            mono_font_name = register_font(mono_path, "MonoFont")
        except Exception:
            pass
    styles = build_styles(font_name, theme_colors, mono_font_name=mono_font_name)
```

- [ ] **Step 2.8: Run full suite**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 66 tests pass.

- [ ] **Step 2.9: Commit**

```bash
cd /Users/TL_1/Desktop/工作/工作
git add md2pdf/scripts/md2pdf.py md2pdf/scripts/test_md2pdf.py
git commit -m "feat: code block uses #f6f8fa bg and monospace font"
```

---
## Task 3: Blockquote left border bar

**GitHub behavior:** Blockquotes have a 4px left border in `#dfe2e5`, text is muted gray, left padding ~16px.

**Current behavior:** Only left indent + muted text, no visible border.

**Approach:** Wrap each blockquote `Paragraph` in a single-cell `Table` with `LINEBEFORE` TableStyle command. Add `blockquote_bar` theme key (github: `#dfe2e5`, others: same as `muted`).

**Files:**
- Modify: `scripts/md2pdf.py` — `THEMES`, `resolve_theme()`, `tokens_to_flowables()`
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 3.1: Write failing test**

```python
def test_blockquote_flowable_is_table_with_left_bar():
    """Blockquote must render as a Table (for left border), not a plain Paragraph."""
    from reportlab.platypus import Table as RLTable
    md2pdf.register_font(BUNDLED_FONT, "BqFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("BqFont", colors_github)
    tokens = [{"type": "blockquote", "text": "A quote"}]
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors_github, "BqFont")
    assert len(flowables) == 1
    assert isinstance(flowables[0], RLTable), \
        f"Expected Table for blockquote, got {type(flowables[0])}"
```

- [ ] **Step 3.2: Run test to confirm RED**

```bash
python -m pytest scripts/test_md2pdf.py::test_blockquote_flowable_is_table_with_left_bar -v 2>&1 | tail -10
```

Expected: FAIL — currently returns `Paragraph`.

- [ ] **Step 3.3: Add `blockquote_bar` to github THEMES entry**

```python
    "github":   {"accent": "#0366d6", "dark": "#24292e", "muted": "#6a737d",
                 "heading_color": "#24292e", "separator_color": "#eaecef",
                 "table_header_bg": "#f6f8fa", "table_header_fg": "#24292e",
                 "code_color": "#0550ae", "code_bg": "#f6f8fa",
                 "blockquote_bar": "#dfe2e5"},
```

- [ ] **Step 3.4: Extend `resolve_theme` to return `blockquote_bar`**

In `else` branch add: `blockquote_bar = t.get("blockquote_bar", muted)`
In `custom` branch add: `blockquote_bar = muted`
Return dict: `"blockquote_bar": hex_to_color(blockquote_bar),`

- [ ] **Step 3.5: Update `tokens_to_flowables` blockquote branch**

Replace:
```python
        elif t == "blockquote":
            xml = inline_to_xml(tok["text"], font_name)
            flowables.append(Paragraph(xml, styles["blockquote"]))
```

With:
```python
        elif t == "blockquote":
            xml = inline_to_xml(tok["text"], font_name)
            para = Paragraph(xml, styles["blockquote"])
            bq_tbl = Table([[para]], colWidths=["100%"])
            bq_tbl.setStyle(TableStyle([
                ("LINEBEFORE", (0, 0), (0, -1), 4,
                 theme_colors["blockquote_bar"]),
                ("LEFTPADDING",  (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING",   (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING",(0, 0), (-1, -1), 2),
                ("BOX", (0, 0), (-1, -1), 0, colors.white),
            ]))
            flowables.append(bq_tbl)
```

- [ ] **Step 3.6: Run full suite**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 67 tests pass.

- [ ] **Step 3.7: Commit**

```bash
cd /Users/TL_1/Desktop/工作/工作
git add md2pdf/scripts/md2pdf.py md2pdf/scripts/test_md2pdf.py
git commit -m "feat: blockquote renders with left border bar"
```

---

## Task 4: Table column alignment (`:---:`, `:---`, `---:`)

**GitHub behavior:** GFM separator row encodes alignment: `:---` = left, `---:` = right, `:---:` = center.

**Current behavior:** Separator row skipped entirely, all columns default to left.

**Files:**
- Modify: `scripts/md2pdf.py` — `_build_table()` (~line 429)
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 4.1: Write failing test**

```python
def test_table_column_alignment():
    """Table separator :---: must produce ALIGN CENTER, ---: must produce RIGHT."""
    md2pdf.register_font(BUNDLED_FONT, "TblAlignFont")
    colors_n = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("TblAlignFont", colors_n)
    lines = ["| L | C | R |", "|:---|:---:|---:|", "| a | b | c |"]
    tbl = md2pdf._build_table(lines, styles, colors_n, "TblAlignFont")
    assert tbl is not None
    # _linecmds holds ALIGN commands after setStyle
    align_cmds = [(cmd[1], cmd[2], cmd[3]) for cmd in tbl._linecmds
                  if cmd[0] == "ALIGN"]
    center_found = any(c[0] == (1, 0) and c[2] == "CENTER" for c in align_cmds)
    right_found  = any(c[0] == (2, 0) and c[2] == "RIGHT"  for c in align_cmds)
    assert center_found, f"Expected CENTER for col 1, got: {align_cmds}"
    assert right_found,  f"Expected RIGHT for col 2, got: {align_cmds}"
```

- [ ] **Step 4.2: Run test to confirm RED**

```bash
python -m pytest scripts/test_md2pdf.py::test_table_column_alignment -v 2>&1 | tail -10
```

Expected: FAIL.

- [ ] **Step 4.3: Update `_build_table` to parse alignment from separator row**

Replace the current `_build_table` function body:

```python
def _build_table(lines: list, styles: dict, theme_colors: dict, font_name: str):
    """Parse GFM table lines into a ReportLab Table."""
    rows = []
    alignments = []  # per-column: "LEFT", "CENTER", or "RIGHT"

    for line in lines:
        # Separator row — parse alignment markers, skip as data
        if re.match(r'^[\s|:\-]+$', line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            for cell in cells:
                if cell.startswith(":") and cell.endswith(":"):
                    alignments.append("CENTER")
                elif cell.endswith(":"):
                    alignments.append("RIGHT")
                else:
                    alignments.append("LEFT")
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return None

    table_data = []
    for r_idx, row in enumerate(rows):
        cell_row = []
        for cell in row:
            xml = inline_to_xml(cell, font_name)
            style = styles["table_header"] if r_idx == 0 else styles["table_cell"]
            cell_row.append(Paragraph(xml, style))
        table_data.append(cell_row)

    tbl = Table(table_data, repeatRows=1, hAlign="LEFT")
    style_cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), theme_colors["table_header_bg"]),
        ("TEXTCOLOR",  (0, 0), (-1, 0), theme_colors["table_header_fg"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.Color(0.97, 0.97, 0.97), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]
    for col_idx, align in enumerate(alignments):
        if align in ("CENTER", "RIGHT"):
            style_cmds.append(("ALIGN", (col_idx, 0), (col_idx, -1), align))
    tbl.setStyle(TableStyle(style_cmds))
    return tbl
```

- [ ] **Step 4.4: Run full suite**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 68 tests pass.

- [ ] **Step 4.5: Commit**

```bash
cd /Users/TL_1/Desktop/工作/工作
git add md2pdf/scripts/md2pdf.py md2pdf/scripts/test_md2pdf.py
git commit -m "feat: table column alignment from GFM separator row"
```

---
## Task 5: Task list `- [ ]` and `- [x]`

**GitHub behavior:** `- [ ] item` renders as ☐ item, `- [x] item` renders as ☑ item.

**Current behavior:** Parsed as regular bullet with literal `[ ]` or `[x]` in text.

**Files:**
- Modify: `scripts/md2pdf.py` — `parse_markdown()` (~line 308), `tokens_to_flowables()` (~line 372)
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 5.1: Write failing tests**

```python
def test_parse_task_list_unchecked():
    """- [ ] item must produce token type 'task' with checked=False."""
    tokens = md2pdf.parse_markdown("- [ ] todo item")
    tasks = [t for t in tokens if t["type"] == "task"]
    assert len(tasks) == 1
    assert tasks[0]["checked"] is False
    assert tasks[0]["text"] == "todo item"


def test_parse_task_list_checked():
    """- [x] item must produce token type 'task' with checked=True."""
    tokens = md2pdf.parse_markdown("- [x] done item")
    tasks = [t for t in tokens if t["type"] == "task"]
    assert len(tasks) == 1
    assert tasks[0]["checked"] is True


def test_task_list_renders_checkbox_symbol():
    """Task token must render ☐ or ☑ prefix, not '[ ]' or '[x]'."""
    from reportlab.platypus import Paragraph as RLPara
    md2pdf.register_font(BUNDLED_FONT, "TaskFont")
    colors_n = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("TaskFont", colors_n)
    tokens = [
        {"type": "task", "text": "todo", "checked": False, "indent": 0},
        {"type": "task", "text": "done", "checked": True,  "indent": 0},
    ]
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors_n, "TaskFont")
    texts = [f.text for f in flowables if isinstance(f, RLPara)]
    assert any("\u2610" in t for t in texts), f"Expected ☐ in {texts}"
    assert any("\u2611" in t for t in texts), f"Expected ☑ in {texts}"
    assert not any("[ ]" in t for t in texts)
    assert not any("[x]" in t for t in texts)
```

- [ ] **Step 5.2: Run tests to confirm RED**

```bash
python -m pytest scripts/test_md2pdf.py::test_parse_task_list_unchecked scripts/test_md2pdf.py::test_parse_task_list_checked scripts/test_md2pdf.py::test_task_list_renders_checkbox_symbol -v 2>&1 | tail -15
```

Expected: all 3 FAIL.

- [ ] **Step 5.3: Update `parse_markdown` — add task list before bullet check**

In `parse_markdown`, add this block immediately before the `# Unordered list item` comment:

```python
        # Task list item - [ ] or - [x] (must come before bullet check)
        m = re.match(r'^(\s*)[-*+]\s+\[([ xX])\]\s+(.*)', line)
        if m:
            indent = len(m.group(1)) // 2
            checked = m.group(2).lower() == "x"
            tokens.append({"type": "task", "text": m.group(3),
                           "checked": checked, "indent": indent})
            i += 1
            continue
```

- [ ] **Step 5.4: Update `tokens_to_flowables` — add task branch after bullet branch**

Add after the `elif t == "bullet":` block:

```python
        elif t == "task":
            indent = tok.get("indent", 0)
            checkbox = "\u2611" if tok["checked"] else "\u2610"
            xml = inline_to_xml(tok["text"], font_name)
            style = ParagraphStyle(
                f"task_{indent}",
                parent=styles["bullet"],
                leftIndent=18 + indent * 16,
                bulletIndent=6 + indent * 16,
            )
            flowables.append(Paragraph(f"{checkbox} {xml}", style))
```

- [ ] **Step 5.5: Run full suite**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 71 tests pass.

- [ ] **Step 5.6: Commit**

```bash
cd /Users/TL_1/Desktop/工作/工作
git add md2pdf/scripts/md2pdf.py md2pdf/scripts/test_md2pdf.py
git commit -m "feat: task list - [ ] and - [x] render as checkbox symbols"
```

---

## Task 6: H3 font size — align to GitHub's 1.25em ratio

**GitHub behavior:** H3 = 1.25em × 16px = 20px ≈ 15pt. Current: 14pt.

**Files:**
- Modify: `scripts/md2pdf.py` — `build_styles()` h3 entry (~line 170)
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 6.1: Write failing test**

```python
def test_h3_fontsize_is_15pt():
    """H3 must be 15pt to match GitHub's 1.25em ratio (was 14pt)."""
    md2pdf.register_font(BUNDLED_FONT, "H3SizeFont")
    colors_n = md2pdf.resolve_theme("navy", {})
    styles = md2pdf.build_styles("H3SizeFont", colors_n)
    assert styles["h3"].fontSize == 15, \
        f"Expected h3 fontSize=15, got {styles['h3'].fontSize}"
```

- [ ] **Step 6.2: Run test to confirm RED**

```bash
python -m pytest scripts/test_md2pdf.py::test_h3_fontsize_is_15pt -v 2>&1 | tail -10
```

Expected: FAIL — currently 14pt.

- [ ] **Step 6.3: Update h3 fontSize in `build_styles`**

Change:
```python
        "h3": ParagraphStyle("h3", fontSize=14, spaceAfter=6,  spaceBefore=10,
                             textColor=heading, fontName=font_name, leading=20),
```

To:
```python
        "h3": ParagraphStyle("h3", fontSize=15, spaceAfter=6,  spaceBefore=10,
                             textColor=heading, fontName=font_name, leading=21),
```

- [ ] **Step 6.4: Run full suite**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 72 tests pass.

- [ ] **Step 6.5: Commit**

```bash
cd /Users/TL_1/Desktop/工作/工作
git add md2pdf/scripts/md2pdf.py md2pdf/scripts/test_md2pdf.py
git commit -m "feat: h3 font size 14pt -> 15pt to match GitHub 1.25em ratio"
```

---

## Task 7: Sync, integration test, and push

**Files:**
- Sync: `~/.claude/skills/md2pdf/scripts/md2pdf.py`
- Sync: `~/.claude/skills/md2pdf/scripts/test_md2pdf.py`

- [ ] **Step 7.1: Run full suite one final time**

```bash
cd /Users/TL_1/Desktop/工作/工作/md2pdf
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 72 tests, all pass.

- [ ] **Step 7.2: Smoke test with real file**

```bash
python scripts/md2pdf.py \
  --input /Users/TL_1/Desktop/工作/工作/DigitalLife/数字生命调研报告.md \
  --output /tmp/test_polish.pdf \
  --font assets/fonts/NotoSansSC-Regular.ttf \
  --theme github \
  --no-cover
```

Expected: `完成 / Done: /tmp/test_polish.pdf (XXX KB)` with no errors.

- [ ] **Step 7.3: Sync to skills directory**

```bash
cp /Users/TL_1/Desktop/工作/工作/md2pdf/scripts/md2pdf.py \
   /Users/TL_1/.claude/skills/md2pdf/scripts/md2pdf.py

cp /Users/TL_1/Desktop/工作/工作/md2pdf/scripts/test_md2pdf.py \
   /Users/TL_1/.claude/skills/md2pdf/scripts/test_md2pdf.py
```

- [ ] **Step 7.4: Run suite from skills path**

```bash
python -m pytest /Users/TL_1/.claude/skills/md2pdf/scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 72 tests, all pass.

- [ ] **Step 7.5: Push to git**

```bash
cd /Users/TL_1/Desktop/工作/工作
git add md2pdf/scripts/md2pdf.py md2pdf/scripts/test_md2pdf.py
git push origin feat/github-theme
```

---

## Self-Review

**Spec coverage:**

| Requirement | Task |
|-------------|------|
| Inline code color `#0550ae` + background | Task 1 |
| Code block `#f6f8fa` bg + monospace font | Task 2 |
| Blockquote left border bar `#dfe2e5` | Task 3 |
| Table column alignment `:---:` / `---:` | Task 4 |
| Task list `- [ ]` / `- [x]` → ☐/☑ | Task 5 |
| H3 font size 15pt (GitHub 1.25em) | Task 6 |
| Sync + integration test | Task 7 |

**Placeholder scan:** None. All steps contain exact code.

**Type consistency:** `resolve_theme` returns extended dict with `code_color`, `code_bg`, `blockquote_bar`. All callers use `theme_colors["key"]` — consistent throughout. `build_styles` new `mono_font_name=None` param is backward-compatible.
