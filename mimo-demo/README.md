# MiMo Code Review Agent 🤖

基于 **Xiaomi MiMo** 大模型的自动化代码审查 Agent，支持多语言代码分析、安全漏洞检测、代码质量评估。

## ✨ 功能特性

- 🔍 **智能代码审查**：自动分析代码质量、风格、潜在 Bug
- 🛡️ **安全漏洞检测**：识别 SQL 注入、XSS、硬编码密钥等安全问题
- 📊 **质量评分**：自动生成 0-100 的代码质量评分及改进建议
- 🔗 **GitHub 集成**：支持自动审查 PR 并生成评论
- 🤖 **多 Agent 协作**：安全 Agent + 质量 Agent + 风格 Agent 并行分析

## 🏗️ 架构

```
用户输入代码/PR
       │
       ▼
┌─────────────────┐
│   Orchestrator   │  ← 主调度 Agent
└────────┬────────┘
         │
    ┌────┼────┐
    ▼    ▼    ▼
┌─────┐┌─────┐┌─────┐
│安全  ││质量  ││风格  │  ← 3 个专业子 Agent
│Agent ││Agent ││Agent │
└──┬──┘└──┬──┘└──┬──┘
   │      │      │
   ▼      ▼      ▼
┌─────────────────┐
│  Report Merger   │  ← 合并分析结果
└────────┬────────┘
         ▼
   📄 审查报告
```

## 🚀 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 配置

```bash
export MIMO_API_KEY="your-api-key"
export GITHUB_TOKEN="your-github-token"  # 可选，用于 GitHub PR 审查
```

### 使用

```bash
# 审查单个文件
python code_reviewer.py review --file path/to/code.py

# 审查整个目录
python code_reviewer.py review --dir ./src

# 审查 GitHub PR
python code_reviewer.py pr --repo owner/repo --pr 42

# 批量审查（适合团队使用）
python code_reviewer.py batch --config team_config.yaml
```

## 📝 示例输出

```
╭──────────────────────────────────────────────╮
│         MiMo Code Review Report              │
│         2024-04-29 17:00:00                  │
├──────────────────────────────────────────────┤
│ 📁 File: src/auth/login.py                   │
│ 📊 Score: 72/100                             │
│                                              │
│ 🛡️ Security Issues (2):                      │
│   ⚠️ [HIGH] Line 45: SQL injection risk      │
│      → Use parameterized queries             │
│   ⚠️ [MED] Line 89: Hardcoded secret         │
│      → Move to environment variables         │
│                                              │
│ 🔍 Quality Issues (3):                       │
│   ℹ️ Line 12: Function too long (120 lines)   │
│      → Split into smaller functions          │
│   ℹ️ Line 67: Missing type hints              │
│      → Add type annotations                  │
│   ℹ️ Line 102: Unused import                  │
│      → Remove unused import                  │
│                                              │
│ 💡 Suggestions:                              │
│   • Add error handling for API calls         │
│   • Consider using async/await for I/O       │
│   • Add docstrings to public methods         │
╰──────────────────────────────────────────────╯
```

## 📁 项目结构

```
mimo-demo/
├── README.md
├── requirements.txt
├── code_reviewer.py      # 主程序
├── agents/
│   ├── orchestrator.py   # 调度 Agent
│   ├── security.py       # 安全分析 Agent
│   ├── quality.py        # 质量分析 Agent
│   └── style.py          # 风格分析 Agent
├── github_integration.py # GitHub PR 集成
├── report_generator.py   # 报告生成
└── examples/
    ├── example_output.md # 示例输出
    └── team_config.yaml  # 团队配置示例
```

## 🔧 技术栈

- **Python 3.10+**
- **Xiaomi MiMo API** - 核心推理引擎
- **Pydantic** - 数据校验
- **Rich** - 终端美化输出
- **PyGithub** - GitHub API 集成

## 📄 License

MIT
