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

## How it works / 技术说明

Tableau Public does not support copying sheets between workbooks via the GUI. This skill documents a Python-based approach — treating `.twbx` files as ZIP archives and merging their XML directly — along with hard-won lessons about Tableau's strict XML content model.

Tableau Public 不支持通过界面跨工作簿复制工作表。本 skill 记录了一种 Python 方案——将 `.twbx` 视为 ZIP 压缩包直接合并其 XML——以及调试过程中总结的 Tableau XML 内容模型规则。

---

## How to use / 使用方式

Install the skill once (see below), then open your project folder in Claude Code and type `/tableaumerger`. Tell Claude which files you want to merge and how you'd like the dashboard laid out — it will generate a `merge_twbx.py` script tailored to your specific files. Run the script, and you're done.

The `merge_twbx.py` included in this repo is the script generated for the original project (6 files, 8 charts). It is provided as a reference example, not a ready-to-run script for other projects.

安装好 skill 之后（见下方），在 Claude Code 中打开你的项目文件夹，输入 `/tableaumerger`，告诉 Claude 你有哪些文件、想要什么样的仪表板布局——它会根据你的实际情况生成一份专属的 `merge_twbx.py` 脚本，运行脚本即可。

本仓库中附带的 `merge_twbx.py` 是原始项目（6 个文件、8 张图）使用的脚本，仅供参考，不能直接用于其他项目。

---

## Install the skill / 安装

### Method 1 — One command / 方法一：一行命令（推荐）

Open a terminal and run:
打开终端，运行：

```powershell
# Windows (PowerShell)
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\commands"; Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Hanaaa-Sying/tableau-merger/main/.claude/skills/tableau-merger/tableau-merger.md" -OutFile "$env:USERPROFILE\.claude\commands\tableaumerger.md"
```

```bash
# macOS / Linux
mkdir -p ~/.claude/commands && curl -o ~/.claude/commands/tableaumerger.md https://raw.githubusercontent.com/Hanaaa-Sying/tableau-merger/main/.claude/skills/tableau-merger/tableau-merger.md
```

### Method 2 — Manual download / 方法二：手动下载

1. Open `.claude/skills/tableau-merger/tableau-merger.md` in this repo
   打开本仓库中的 `.claude/skills/tableau-merger/tableau-merger.md`
2. Click **Raw**, then save the file (Ctrl+S / Cmd+S)
   点击 **Raw**，然后保存文件
3. Move it to `C:\Users\你的用户名\.claude\commands\` (Windows) or `~/.claude/commands/` (macOS/Linux) — create the folder if it doesn't exist
   将文件移动到 `C:\Users\你的用户名\.claude\commands\`（Windows）或 `~/.claude/commands/`（macOS/Linux），文件夹不存在则新建

Then in Claude Code, type `/tableaumerger` to invoke it.

安装后在 Claude Code 中输入 `/tableaumerger` 即可调用。

---

## Requirements / 环境要求

- Claude Code (desktop app or CLI)
- Python 3.x（standard library only, no pip installs / 仅标准库，无需 pip）
- Tableau Public desktop app / Tableau Public 桌面版
- All `.twbx` files must share the same data schema / 所有 `.twbx` 文件须使用相同字段结构的数据
