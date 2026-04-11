# md2pdf

将 Markdown 文件转换为专业排版 PDF 的 Claude Code skill。纯 Python 实现，无需浏览器，完整支持中文。

## 功能

- 6 种内置主题（navy、minimal、warm、slate、gold、midnight），方框选择界面含 ANSI 色块预览
- 自动检测系统字体，支持 PostScript OTF 自动转换（via fontTools），内置 NotoSansSC 作为后备
- 代码块完整支持中文（使用选定字体渲染，不再乱码）
- 支持封面页（回车选默认标题，元信息自动填入当前日期）、页眉页脚
- 通过 `pdf_style.yaml` 自定义默认字体、主题等
- 中英双语交互界面

## 使用方式

在 Claude Code 中直接说：

```
把 report.md 转成 PDF，用 navy 主题
convert /path/to/notes.md to pdf, no cover page
md2pdf ~/Documents/proposal.md
```

Skill 会自动引导你选择字体和主题，然后生成 PDF。

## 文件结构

```
md2pdf/
├── SKILL.md                    # Skill 入口（Claude 读取）
├── scripts/
│   ├── md2pdf.py               # PDF 生成主脚本
│   └── font_finder.py          # 系统字体扫描 + yaml 缓存
├── assets/
│   └── fonts/
│       └── NotoSansSC-Regular.ttf   # 内置中文字体（后备）
└── references/
    └── style_schema.md         # pdf_style.yaml 字段说明
```

## 样式配置

在项目目录下创建 `pdf_style.yaml` 可自定义默认行为：

```yaml
default_font: PingFang SC       # 默认字体（首次选择后自动写入）
theme: navy                     # 默认主题

page_size: A4
margin_cm: 2.5

cover: true
cover_title: ""                 # 留空则自动提取第一个 H1

header: true
footer: true
```

完整字段说明见 `references/style_schema.md`。

## 主题列表

| 主题 | 风格 |
|------|------|
| navy | 深海军蓝，专业商务 |
| minimal | 黑白极简 |
| warm | 暖棕，人文学术 |
| slate | 石板灰，低调稳重 |
| gold | 金棕，高端商务 |
| midnight | 午夜黑，极简暗色 |
| custom | 自定义 hex 颜色 |

## 依赖

```bash
pip install reportlab PyYAML
```

## 安装到 Claude Code

将本目录放到 Claude Code 可访问的路径下，或推送到 GitHub 后通过 skill 管理器安装。

GitHub: https://github.com/tl0431/skills/tree/main/md2pdf
