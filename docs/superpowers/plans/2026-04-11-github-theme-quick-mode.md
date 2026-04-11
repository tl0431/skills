# GitHub Theme & Quick Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `github` theme that fully aligns with GitHub's markdown preview style, extend the theme color system to support per-theme heading/table/separator colors, and add a quick/custom mode selector to the skill flow.

**Architecture:** Extend `resolve_theme()` to return 4 new color keys (`heading_color`, `separator_color`, `table_header_bg`, `table_header_fg`) with defaults matching current behavior so all existing themes stay unchanged. The `github` theme overrides these keys to match GitHub's CSS. `build_styles`, `tokens_to_flowables`, and `_build_table` are updated to consume the new keys. SKILL.md gets a new Step 1.5 that branches quick/custom before font and theme selection.

**Tech Stack:** Python 3, ReportLab, PyYAML, pytest — same as existing codebase.

---

## File Map

| File | Change |
|------|--------|
| `scripts/md2pdf.py` | Add `github` to `THEMES`; extend `resolve_theme` return dict; update `build_styles`, `tokens_to_flowables`, `_build_table` |
| `scripts/test_md2pdf.py` | New tests per task (TDD) |
| `~/.claude/skills/md2pdf/SKILL.md` | Add Step 1.5 quick/custom branch |
| `~/.claude/skills/md2pdf/scripts/md2pdf.py` | Sync from local after all tasks pass |
| `~/.claude/skills/md2pdf/scripts/test_md2pdf.py` | Sync from local after all tasks pass |

All edits happen in `/Users/TL_1/Desktop/工作/工作/md2pdf/scripts/`. Sync to `~/.claude/skills/md2pdf/scripts/` only at the end.

---

## Task 1: Extend `resolve_theme` with 4 new color keys

**Files:**
- Modify: `scripts/md2pdf.py` — `resolve_theme()` function (~line 74)
- Test: `scripts/test_md2pdf.py`

The 4 new keys and their defaults for existing themes:

| Key | Existing themes default | GitHub value |
|-----|------------------------|-------------|
| `heading_color` | same as `accent` | `#24292e` (dark, same as body) |
| `separator_color` | same as `accent` | `#eaecef` (light gray) |
| `table_header_bg` | same as `accent` | `#f6f8fa` (very light gray) |
| `table_header_fg` | `#ffffff` (white) | `#24292e` (dark) |

- [ ] **Step 1.1: Write failing tests**

Add to `scripts/test_md2pdf.py` after the existing `test_unknown_theme_falls_back_to_navy` test:

```python
def test_resolve_theme_returns_heading_color():
    """All themes must return heading_color key."""
    for name in list(md2pdf.THEMES.keys()) + ["navy", "custom"]:
        c = md2pdf.resolve_theme(name, {})
        assert "heading_color" in c, f"Missing heading_color for theme {name}"
        assert "separator_color" in c
        assert "table_header_bg" in c
        assert "table_header_fg" in c


def test_existing_themes_heading_color_equals_accent():
    """For non-github themes, heading_color must equal accent (backward compat)."""
    for name in ["navy", "minimal", "warm", "slate", "gold", "midnight"]:
        c = md2pdf.resolve_theme(name, {})
        assert c["heading_color"].hexval() == c["accent"].hexval(), \
            f"{name}: heading_color {c['heading_color'].hexval()} != accent {c['accent'].hexval()}"


def test_github_theme_heading_color_is_dark():
    """GitHub theme: heading_color must equal dark (#24292e), not accent (#0366d6)."""
    c = md2pdf.resolve_theme("github", {})
    assert c["heading_color"].hexval() == c["dark"].hexval()
    # accent is blue, heading is dark — they must differ
    assert c["heading_color"].hexval() != c["accent"].hexval()


def test_github_theme_separator_is_light_gray():
    """GitHub theme: separator_color must be #eaecef (light gray)."""
    c = md2pdf.resolve_theme("github", {})
    # #eaecef = rgb(234, 236, 239) ≈ Color(0.918, 0.925, 0.937)
    assert c["separator_color"].red > 0.9
    assert c["separator_color"].green > 0.9
    assert c["separator_color"].blue > 0.9


def test_github_theme_table_header_is_light_bg_dark_fg():
    """GitHub theme: table header must be light background with dark text."""
    c = md2pdf.resolve_theme("github", {})
    # Light background: all channels > 0.9
    bg = c["table_header_bg"]
    assert bg.red > 0.9 and bg.green > 0.9 and bg.blue > 0.9
    # Dark foreground: all channels < 0.2
    fg = c["table_header_fg"]
    assert fg.red < 0.2 and fg.green < 0.2 and fg.blue < 0.2
```

- [ ] **Step 1.2: Run tests to confirm RED**

```bash
cd /Users/TL_1/Desktop/工作/工作/md2pdf
python -m pytest scripts/test_md2pdf.py::test_resolve_theme_returns_heading_color scripts/test_md2pdf.py::test_github_theme_heading_color_is_dark scripts/test_md2pdf.py::test_github_theme_separator_is_light_gray scripts/test_md2pdf.py::test_github_theme_table_header_is_light_bg_dark_fg -v 2>&1 | tail -20
```

Expected: all 5 new tests FAIL.

- [ ] **Step 1.3: Add `github` to `THEMES` dict**

In `scripts/md2pdf.py`, add to the `THEMES` dict (after `"olive"`):

```python
    "github":   {"accent": "#0366d6", "dark": "#24292e", "muted": "#6a737d",
                 "heading_color": "#24292e", "separator_color": "#eaecef",
                 "table_header_bg": "#f6f8fa", "table_header_fg": "#24292e"},
```

- [ ] **Step 1.4: Extend `resolve_theme` to return the 4 new keys**

Replace the existing `resolve_theme` function body:

```python
def resolve_theme(theme_name: str, style_data: dict) -> dict:
    """Return color dict for the given theme. Includes accent, dark, muted,
    heading_color, separator_color, table_header_bg, table_header_fg."""
    if theme_name == "custom":
        accent = style_data.get("custom_accent", "#333333")
        dark   = style_data.get("custom_dark",   "#111111")
        muted  = style_data.get("custom_muted",  "#888888")
        heading_color    = accent
        separator_color  = accent
        table_header_bg  = accent
        table_header_fg  = "#ffffff"
    else:
        t = THEMES.get(theme_name, THEMES["navy"])
        accent = t["accent"]
        dark   = t["dark"]
        muted  = t["muted"]
        # Extended keys — fall back to accent/white if not specified (all existing themes)
        heading_color   = t.get("heading_color",   accent)
        separator_color = t.get("separator_color", accent)
        table_header_bg = t.get("table_header_bg", accent)
        table_header_fg = t.get("table_header_fg", "#ffffff")

    return {
        "accent":          hex_to_color(accent),
        "dark":            hex_to_color(dark),
        "muted":           hex_to_color(muted),
        "heading_color":   hex_to_color(heading_color),
        "separator_color": hex_to_color(separator_color),
        "table_header_bg": hex_to_color(table_header_bg),
        "table_header_fg": hex_to_color(table_header_fg),
    }
```

- [ ] **Step 1.5: Run tests to confirm GREEN**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: all tests pass (52 existing + 5 new = 57 total).

---

## Task 2: Use `heading_color` in `build_styles` and `separator_color` in `tokens_to_flowables`

**Files:**
- Modify: `scripts/md2pdf.py` — `build_styles()` (~line 136), `tokens_to_flowables()` (~line 337)
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 2.1: Write failing tests**

Add after `test_build_styles_has_required_keys`:

```python
def test_build_styles_h1_uses_heading_color():
    """h1/h2/h3 styles must use heading_color, not accent."""
    md2pdf.register_font(BUNDLED_FONT, "HeadColorFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("HeadColorFont", colors_github)
    # GitHub: heading_color == dark, accent == blue — they differ
    assert styles["h1"].textColor == colors_github["heading_color"]
    assert styles["h1"].textColor != colors_github["accent"]
    assert styles["h2"].textColor == colors_github["heading_color"]
    assert styles["h3"].textColor == colors_github["heading_color"]


def test_tokens_to_flowables_uses_separator_color_for_h1_hr():
    """HRFlowable after h1/h2 must use separator_color, not accent."""
    from reportlab.platypus import HRFlowable as RLHRFlowable
    md2pdf.register_font(BUNDLED_FONT, "SepColorFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("SepColorFont", colors_github)
    tokens = [{"type": "h1", "text": "Title"}]
    flowables = md2pdf.tokens_to_flowables(tokens, styles, colors_github, "SepColorFont")
    hr_flowables = [f for f in flowables if isinstance(f, RLHRFlowable)]
    assert len(hr_flowables) == 1
    # separator_color for github is #eaecef (light gray), accent is #0366d6 (blue)
    assert hr_flowables[0]._color == colors_github["separator_color"]
    assert hr_flowables[0]._color != colors_github["accent"]
```

- [ ] **Step 2.2: Run tests to confirm RED**

```bash
python -m pytest scripts/test_md2pdf.py::test_build_styles_h1_uses_heading_color scripts/test_md2pdf.py::test_tokens_to_flowables_uses_separator_color_for_h1_hr -v 2>&1 | tail -15
```

Expected: both tests FAIL.

- [ ] **Step 2.3: Update `build_styles` to use `heading_color`**

In `build_styles`, add `heading = theme_colors["heading_color"]` after the `muted` line, then change h1/h2/h3 `textColor` to use `heading`:

```python
def build_styles(font_name: str, theme_colors: dict) -> dict:
    """Return a dict of ParagraphStyle objects keyed by role."""
    accent  = theme_colors["accent"]
    dark    = theme_colors["dark"]
    muted   = theme_colors["muted"]
    heading = theme_colors["heading_color"]   # ← new

    base = dict(fontName=font_name, textColor=dark, leading=20)

    return {
        "h1": ParagraphStyle("h1", fontSize=24, spaceAfter=12, spaceBefore=18,
                             textColor=heading, fontName=font_name, leading=30),
        "h2": ParagraphStyle("h2", fontSize=18, spaceAfter=8,  spaceBefore=14,
                             textColor=heading, fontName=font_name, leading=24),
        "h3": ParagraphStyle("h3", fontSize=14, spaceAfter=6,  spaceBefore=10,
                             textColor=heading, fontName=font_name, leading=20),
        "h4": ParagraphStyle("h4", fontSize=12, spaceAfter=4,  spaceBefore=8,
                             textColor=dark,   fontName=font_name, leading=18),
        "h5": ParagraphStyle("h5", fontSize=11, spaceAfter=4,  spaceBefore=6,
                             textColor=dark,   fontName=font_name, leading=16),
        "h6": ParagraphStyle("h6", fontSize=10, spaceAfter=2,  spaceBefore=4,
                             textColor=muted,  fontName=font_name, leading=15),
        "body": ParagraphStyle("body", fontSize=11, spaceAfter=6, spaceBefore=2,
                               **base),
        "bullet": ParagraphStyle("bullet", fontSize=11, spaceAfter=4, spaceBefore=2,
                                 leftIndent=18, bulletIndent=6, **base),
        "code_inline": ParagraphStyle("code_inline", fontSize=10, spaceAfter=4,
                                      fontName=font_name, textColor=dark, leading=16),
        "code_block": ParagraphStyle("code_block", fontSize=9, spaceAfter=8,
                                     spaceBefore=4, fontName=font_name,
                                     textColor=dark, leading=14,
                                     leftIndent=12, backColor=colors.Color(0.95, 0.95, 0.95)),
        "blockquote": ParagraphStyle("blockquote", fontSize=11, spaceAfter=6,
                                     spaceBefore=4, leftIndent=20,
                                     textColor=muted, fontName=font_name, leading=18),
        "cover_title": ParagraphStyle("cover_title", fontSize=32, spaceAfter=16,
                                      alignment=TA_CENTER, textColor=accent,
                                      fontName=font_name, leading=40),
        "cover_subtitle": ParagraphStyle("cover_subtitle", fontSize=18, spaceAfter=10,
                                         alignment=TA_CENTER, textColor=dark,
                                         fontName=font_name, leading=24),
        "cover_meta": ParagraphStyle("cover_meta", fontSize=12, spaceAfter=6,
                                     alignment=TA_CENTER, textColor=muted,
                                     fontName=font_name, leading=18),
        "table_header": ParagraphStyle("table_header", fontSize=10, fontName=font_name,
                                       textColor=theme_colors["table_header_fg"], leading=14),
        "table_cell": ParagraphStyle("table_cell", fontSize=10, fontName=font_name,
                                     textColor=dark, leading=14),
    }
```

Note: `table_header` now uses `theme_colors["table_header_fg"]` instead of `colors.white` — this covers Task 3's style concern too.

- [ ] **Step 2.4: Update `tokens_to_flowables` to use `separator_color` for h1/h2 HR**

In `tokens_to_flowables`, find the heading branch and change the HRFlowable color:

```python
        elif t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(t[1])
            xml = inline_to_xml(tok["text"], font_name)
            flowables.append(Paragraph(xml, styles[t]))
            if level <= 2:
                flowables.append(HRFlowable(width="100%", thickness=1,
                                            color=theme_colors["separator_color"],
                                            spaceAfter=4))
```

- [ ] **Step 2.5: Run tests to confirm GREEN**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: all tests pass (57 existing + 2 new = 59 total).

---

## Task 3: Use `table_header_bg` / `table_header_fg` in `_build_table`

**Files:**
- Modify: `scripts/md2pdf.py` — `_build_table()` (~line 407)
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 3.1: Write failing test**

Add after `test_parse_table_multiple_data_rows`:

```python
def test_build_table_github_uses_light_header():
    """_build_table with github theme must use light header background, not blue."""
    md2pdf.register_font(BUNDLED_FONT, "TblGithubFont")
    colors_github = md2pdf.resolve_theme("github", {})
    styles = md2pdf.build_styles("TblGithubFont", colors_github)
    lines = ["| A | B |", "|---|---|", "| 1 | 2 |"]
    tbl = md2pdf._build_table(lines, styles, colors_github, "TblGithubFont")
    assert tbl is not None
    # Find the BACKGROUND command for row 0 in the TableStyle
    bg_cmd = None
    for cmd in tbl._tblStyle._cmds:
        if cmd[0] == "BACKGROUND" and cmd[1] == (0, 0) and cmd[2] == (-1, 0):
            bg_cmd = cmd
    assert bg_cmd is not None, "No BACKGROUND command found for header row"
    header_bg = bg_cmd[3]
    # GitHub table_header_bg is #f6f8fa (light) — all channels > 0.9
    assert header_bg.red > 0.9 and header_bg.green > 0.9 and header_bg.blue > 0.9, \
        f"Expected light header bg, got {header_bg}"
```

- [ ] **Step 3.2: Run test to confirm RED**

```bash
python -m pytest scripts/test_md2pdf.py::test_build_table_github_uses_light_header -v 2>&1 | tail -10
```

Expected: FAIL — header background is blue (#0366d6), not light gray.

- [ ] **Step 3.3: Update `_build_table` to use theme_colors for header**

Replace the `accent = theme_colors["accent"]` line and the two TableStyle commands:

```python
def _build_table(lines: list, styles: dict, theme_colors: dict, font_name: str):
    """Parse GFM table lines into a ReportLab Table."""
    rows = []
    for line in lines:
        # Skip separator rows (---|---)
        if re.match(r'^[\s|:\-]+$', line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return None

    # Build Paragraph cells
    table_data = []
    for r_idx, row in enumerate(rows):
        cell_row = []
        for cell in row:
            xml = inline_to_xml(cell, font_name)
            style = styles["table_header"] if r_idx == 0 else styles["table_cell"]
            cell_row.append(Paragraph(xml, style))
        table_data.append(cell_row)

    tbl = Table(table_data, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), theme_colors["table_header_bg"]),
        ("TEXTCOLOR",  (0, 0), (-1, 0), theme_colors["table_header_fg"]),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.Color(0.97, 0.97, 0.97), colors.white]),
        ("GRID",       (0, 0), (-1, -1), 0.5, colors.Color(0.8, 0.8, 0.8)),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    return tbl
```

- [ ] **Step 3.4: Run tests to confirm GREEN**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: all tests pass (59 existing + 1 new = 60 total).

---

## Task 4: Integration test — full PDF with `github` theme

**Files:**
- Test: `scripts/test_md2pdf.py`

- [ ] **Step 4.1: Write integration test**

Add after `test_convert_chinese_content`:

```python
def test_convert_github_theme(tmp_path):
    """Full PDF conversion with github theme must succeed and produce a valid file."""
    input_md = tmp_path / "github_test.md"
    output_pdf = tmp_path / "github_test.pdf"
    input_md.write_text(
        "# GitHub Style\n\n## Subheading\n\nBody text with **bold** and *italic*.\n\n"
        "| Col A | Col B |\n|-------|-------|\n| Cell 1 | Cell 2 |\n\n"
        "> A blockquote\n\n```python\nprint('hello')\n```\n\n"
        "- Bullet one\n- Bullet two\n\n---\n\n### H3 heading\n",
        encoding="utf-8",
    )
    result = md2pdf.convert(
        input_path=str(input_md),
        output_path=str(output_pdf),
        font_path=BUNDLED_FONT,
        theme_name="github",
    )
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 2000
```

- [ ] **Step 4.2: Run test to confirm it passes**

```bash
python -m pytest scripts/test_md2pdf.py::test_convert_github_theme -v 2>&1 | tail -10
```

Expected: PASS immediately (github theme now works end-to-end).

- [ ] **Step 4.3: Run full suite**

```bash
python -m pytest scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 61 tests, all pass.

---

## Task 5: Update SKILL.md — add quick/custom mode branch

**Files:**
- Modify: `~/.claude/skills/md2pdf/SKILL.md`

No code change, no Python tests. This is a skill flow change only.

- [ ] **Step 5.1: Read current SKILL.md to find insertion point**

```bash
grep -n "Step 2" ~/.claude/skills/md2pdf/SKILL.md | head -5
```

- [ ] **Step 5.2: Insert Step 1.5 between Step 1 and Step 2**

After the Step 1 block (path resolution), insert the following new section **before** "### Step 2: Font selection":

```markdown
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
```

- [ ] **Step 5.3: Verify SKILL.md structure looks correct**

```bash
grep -n "Step" ~/.claude/skills/md2pdf/SKILL.md
```

Expected output shows steps in order: 1, 1.5, 2, 3, 3.5, 4, 5.

---

## Task 6: Sync to skills directory and final verification

**Files:**
- Modify: `~/.claude/skills/md2pdf/scripts/md2pdf.py`
- Modify: `~/.claude/skills/md2pdf/scripts/test_md2pdf.py`

- [ ] **Step 6.1: Sync both files**

```bash
cp /Users/TL_1/Desktop/工作/工作/md2pdf/scripts/md2pdf.py \
   /Users/TL_1/.claude/skills/md2pdf/scripts/md2pdf.py

cp /Users/TL_1/Desktop/工作/工作/md2pdf/scripts/test_md2pdf.py \
   /Users/TL_1/.claude/skills/md2pdf/scripts/test_md2pdf.py
```

- [ ] **Step 6.2: Run full suite from skills path**

```bash
python -m pytest /Users/TL_1/.claude/skills/md2pdf/scripts/test_md2pdf.py -q 2>&1 | tail -5
```

Expected: 61 tests, all pass.

- [ ] **Step 6.3: Smoke test — convert a real file with github theme**

```bash
python /Users/TL_1/.claude/skills/md2pdf/scripts/md2pdf.py \
  --input /Users/TL_1/Desktop/工作/工作/DigitalLife/数字生命调研报告.md \
  --output /tmp/test_github_theme.pdf \
  --font /Users/TL_1/.claude/skills/md2pdf/assets/fonts/NotoSansSC-Regular.ttf \
  --theme github \
  --no-cover
```

Expected: `完成 / Done: /tmp/test_github_theme.pdf (XXX KB)` with no errors.

---

## Self-Review

**Spec coverage check:**

| Requirement | Covered by |
|-------------|-----------|
| `github` theme added to THEMES | Task 1 Step 1.3 |
| `resolve_theme` returns 4 new keys | Task 1 Step 1.4 |
| Existing themes unchanged (heading_color = accent) | Task 1 Step 1.4 + test |
| `build_styles` uses `heading_color` for h1/h2/h3 | Task 2 Step 2.3 |
| `tokens_to_flowables` uses `separator_color` for h1/h2 HR | Task 2 Step 2.4 |
| `_build_table` uses `table_header_bg`/`fg` | Task 3 Step 3.3 |
| Full PDF integration test | Task 4 |
| SKILL.md quick/custom branch | Task 5 |
| Skills directory sync | Task 6 |

**Placeholder scan:** None found. All steps contain exact code.

**Type consistency:** `resolve_theme` returns `dict[str, Color]`. All callers (`build_styles`, `tokens_to_flowables`, `_build_table`, `HeaderFooterCanvas`) use `theme_colors["key"]` — consistent with the extended dict throughout.

**Backward compatibility:** Non-github themes do not have the new keys in `THEMES`. `resolve_theme` falls back to `t.get("heading_color", accent)` — so all existing themes get `heading_color == accent`, which is identical to the current behavior (h1/h2/h3 use accent color). Zero visual change for existing themes.
