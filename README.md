# tableau-merger

A Claude Code slash command (`/tableaumerger`) for merging multiple Tableau `.twbx` files into a single workbook with a dashboard.

一个 Claude Code slash command（`/tableaumerger`），用于将多个 Tableau `.twbx` 文件合并为包含仪表板的单一工作簿。

---

## Background / 背景（这个 skill 是干啥的）

Imagine your team splits up to make charts — each person saves their work as a separate Tableau file. Now you need to combine everything into one dashboard for the final presentation. Simple enough, right? Except Tableau Public (the free version) doesn't actually let you do this through the normal interface. There's no "import" button, and copy-pasting between windows just doesn't work.

This skill solves that problem. You tell it which files to merge and what to call each chart, and it handles the rest automatically — producing a single `.twbx` file with all your charts and a dashboard ready to open in Tableau Public.

想象一下：你们小组分工合作，每人做了一张图，各自保存为一个 Tableau 文件。最后要把所有图拼成一个仪表板交作业，但打开 Tableau Public（免费版）才发现——根本没有"导入"按钮，窗口之间复制粘贴也不管用。

这个 skill 就是用来解决这个问题的。你告诉它要合并哪些文件、每张图叫什么名字，它自动帮你处理好，最终输出一个包含所有图表和仪表板的 `.twbx` 文件，直接用 Tableau Public 打开就行。

---

## Install the skill / 安装

### User-level — available in all projects / 用户级——所有项目可用

```powershell
# Windows
Copy-Item .claude\skills\tableau-merger\tableau-merger.md "$env:USERPROFILE\.claude\commands\"
```

```bash
# macOS / Linux
cp .claude/skills/tableau-merger/tableau-merger.md ~/.claude/commands/
```

### Project-level — available in one project only / 项目级——仅当前项目可用

```powershell
# Windows
Copy-Item .claude\skills\tableau-merger\tableau-merger.md "your\project\.claude\commands\"
```

```bash
# macOS / Linux
cp .claude/skills/tableau-merger/tableau-merger.md your/project/.claude/commands/
```

Then in Claude Code, type `/tableaumerger` to invoke it.

安装后在 Claude Code 中输入 `/tableaumerger` 即可调用。

---

## What's included / 文件说明

| File | Description / 说明 |
|---|---|
| `.claude/skills/tableau-merger/tableau-merger.md` | Slash command definition / slash command 定义 |
| `merge_twbx.py` | Complete working merge script / 完整可运行的合并脚本 |

---

## Requirements / 环境要求

- Python 3.x（standard library only, no pip installs / 仅标准库，无需 pip）
- Tableau Public desktop app / Tableau Public 桌面版
- All `.twbx` files must share the same data schema / 所有 `.twbx` 文件须使用相同字段结构的数据
