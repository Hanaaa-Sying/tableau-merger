# tableau-merger

**EN** A Claude Code slash command (`/tableaumerger`) for merging multiple Tableau `.twbx` files into a single workbook with a dashboard.

**中** 一个 Claude Code slash command（`/tableaumerger`），用于将多个 Tableau `.twbx` 文件合并为包含仪表板的单一工作簿。

---

## Background / 背景

**EN** Tableau Public does not support copying sheets between workbooks via the GUI. This skill documents a Python-based approach — treating `.twbx` files as ZIP archives and merging their XML directly — along with hard-won lessons about Tableau's strict XML content model.

**中** Tableau Public 不支持通过界面跨工作簿复制工作表。本 skill 记录了一种 Python 方案——将 `.twbx` 视为 ZIP 压缩包直接合并其 XML——以及调试过程中总结的 Tableau XML 内容模型规则。

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
