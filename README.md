# DocuMind

DocuMind 是一个 Agentic RAG（检索增强生成）系统，专为文档智能分析而设计。

## 功能特性

- 自动网页爬取和内容提取
- 智能知识库构建
- 基于LangGraph的智能体系统
- 代码生成、执行和修复闭环
- 优雅的命令行界面

## 安装

```bash
pip install poetry
poetry install
```

## 使用

```bash
# 查看帮助
python -m documind.main --help

# 爬取网页
python -m documind.main crawl https://example.com

# 索引文档
python -m documind.main index

# 查询文档
python -m documind.main query "你的问题"

# 运行智能体
python -m documind.main agent "任务描述"
```

## 配置

请在 `.env` 文件中配置 API 密钥：

```
DASHSCOPE_API_KEY=你的阿里云百炼API密钥
```





<div align="center">
  <h1>🤖 DocuMind</h1>
  <p><b>Agentic RAG: The Technical Researcher that Self-Heals its Own Code.</b></p>

  <!-- 徽章部分，显得项目很专业 -->
  <p>
    <img src="https://img.shields.io/github/stars/your-username/DocuMind?style=for-the-badge&color=FFE333" />
    <img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python" />
    <img src="https://img.shields.io/badge/Framework-LangGraph-red?style=for-the-badge" />
    <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
  </p>

  <p>
    <a href="#-key-features">功能特性</a> •
    <a href="#-quick-start">快速开始</a> •
    <a href="#-how-it-works">工作原理</a> •
    <a href="#-roadmap">路线图</a>
  </p>
</div>

---

## 💡 为什么选择 DocuMind?

传统的 RAG 只是“复读”文档。**DocuMind** 走得更远——它不仅阅读文档，还会**验证**它生成的每一行代码。

- **不再有幻觉 (No More Hallucinations)**: 如果生成的代码报错，Agent 会自动阅读报错信息，重新查阅文档并修复。
- **全自动文档解析**: 集成 `Crawl4AI`，自动将复杂的 SPA 网页转化为干净的 Markdown。
- **本地代码验证**: 在隔离沙盒中运行代码，确保给你的答案是真实可用的。

## ✨ 功能特性 (Key Features)

- 🔍 **Deep Research**: 自动抓取技术文档并构建本地向量索引。
- 🔄 **Self-Healing Loop**: 基于 LangGraph 的“生成-运行-报错-修复”闭环。
- 🛠️ **Developer Friendly**: 极致优雅的终端界面，支持语法高亮。
- 🔌 **Multi-Model Support**: 支持阿里云百炼 (Qwen), OpenAI, Claude 及本地 Ollama。

## 📺 演示 (Demo)

> 这里建议放一张你录制的 VHS GIF 动图，展示命令运行过程。

## 🚀 快速开始 (Quick Start)

### 1. 安装
我们推荐使用现代包管理器 **uv** 或 **Poetry**:

```bash
git clone https://github.com/your-username/DocuMind.git
cd DocuMind
pip install -e .