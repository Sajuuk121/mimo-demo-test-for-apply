"""MiMo Code Review Agent - 基于 Xiaomi MiMo 的自动化代码审查工具"""

import os
import json
import asyncio
import argparse
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import httpx
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

# ── Data Models ──────────────────────────────────────────────

class Issue(BaseModel):
    severity: str  # HIGH / MED / LOW / INFO
    line: Optional[int]
    message: str
    suggestion: str

class FileReview(BaseModel):
    file_path: str
    score: int  # 0-100
    issues: list[Issue] = field(default_factory=list)
    summary: str = ""

class ReviewReport(BaseModel):
    files: list[FileReview] = field(default_factory=list)
    overall_score: int = 0
    total_issues: int = 0

# ── MiMo API Client ─────────────────────────────────────────

class MiMoClient:
    """调用 Xiaomi MiMo API 进行代码分析"""

    BASE_URL = "https://api.xiaomimimo.com/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=120)

    async def analyze(self, system_prompt: str, code: str) -> str:
        """发送代码到 MiMo 进行分析"""
        resp = await self.client.post(
            f"{self.BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "MiMo-V2.5",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请分析以下代码：\n\n```\n{code}\n```"},
                ],
                "temperature": 0.1,
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    async def close(self):
        await self.client.aclose()

# ── Sub-Agents ───────────────────────────────────────────────

SECURITY_PROMPT = """你是一个安全分析专家。分析代码中的安全漏洞，返回 JSON 数组：
[{"severity":"HIGH|MED|LOW","line":行号,"message":"问题描述","suggestion":"修复建议"}]
只返回 JSON，不要其他文字。重点关注：SQL注入、XSS、硬编码密钥、路径遍历、不安全的反序列化。"""

QUALITY_PROMPT = """你是一个代码质量分析专家。分析代码质量，返回 JSON 数组：
[{"severity":"INFO|LOW|MED","line":行号,"message":"问题描述","suggestion":"改进建议"}]
只返回 JSON，不要其他文字。重点关注：函数复杂度、重复代码、错误处理、类型提示、命名规范。"""

STYLE_PROMPT = """你是一个代码风格分析专家。分析代码风格，返回 JSON 数组：
[{"severity":"INFO|LOW","line":行号,"message":"问题描述","suggestion":"改进建议"}]
只返回 JSON，不要其他文字。重点关注：PEP8合规、import顺序、注释质量、代码可读性。"""


async def run_agent(client: MiMoClient, prompt: str, code: str) -> list[Issue]:
    """运行单个分析 Agent"""
    try:
        result = await client.analyze(prompt, code)
        # 尝试从回复中提取 JSON
        result = result.strip()
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        items = json.loads(result)
        return [Issue(**item) for item in items]
    except Exception as e:
        console.print(f"[yellow]⚠ Agent 分析异常: {e}[/yellow]")
        return []

# ── Orchestrator ─────────────────────────────────────────────

class CodeReviewer:
    """主调度器：协调多个子 Agent 并行分析代码"""

    def __init__(self, api_key: str):
        self.client = MiMoClient(api_key)

    async def review_file(self, file_path: str) -> FileReview:
        """审查单个文件"""
        code = Path(file_path).read_text(encoding="utf-8", errors="replace")

        console.print(f"[cyan]🔍 正在分析: {file_path}[/cyan]")

        # 三个 Agent 并行执行
        security_task = run_agent(self.client, SECURITY_PROMPT, code)
        quality_task = run_agent(self.client, QUALITY_PROMPT, code)
        style_task = run_agent(self.client, STYLE_PROMPT, code)

        security_issues, quality_issues, style_issues = await asyncio.gather(
            security_task, quality_task, style_task
        )

        all_issues = security_issues + quality_issues + style_issues

        # 计算评分
        score = 100
        for issue in all_issues:
            if issue.severity == "HIGH":
                score -= 15
            elif issue.severity == "MED":
                score -= 8
            elif issue.severity == "LOW":
                score -= 3
            elif issue.severity == "INFO":
                score -= 1
        score = max(0, score)

        return FileReview(
            file_path=file_path,
            score=score,
            issues=all_issues,
            summary=f"发现 {len(all_issues)} 个问题",
        )

    async def review_directory(self, dir_path: str) -> ReviewReport:
        """审查整个目录"""
        files = list(Path(dir_path).rglob("*.py"))
        if not files:
            console.print("[yellow]未找到 Python 文件[/yellow]")
            return ReviewReport()

        reviews = []
        for f in files:
            review = await self.review_file(str(f))
            reviews.append(review)

        total_issues = sum(len(r.issues) for r in reviews)
        avg_score = sum(r.score for r in reviews) // len(reviews) if reviews else 0

        return ReviewReport(
            files=reviews,
            overall_score=avg_score,
            total_issues=total_issues,
        )

    async def close(self):
        await self.client.close()

# ── Report Display ───────────────────────────────────────────

def display_report(report: ReviewReport):
    """在终端中显示审查报告"""
    for fr in report.files:
        table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        table.add_column("Item", style="bold")
        table.add_column("Detail")

        # 评分颜色
        score_color = "green" if fr.score >= 80 else "yellow" if fr.score >= 60 else "red"
        table.add_row("📊 Score", f"[{score_color}]{fr.score}/100[/{score_color}]")

        for issue in fr.issues:
            icon = {"HIGH": "🔴", "MED": "🟡", "LOW": "🔵", "INFO": "ℹ️"}.get(
                issue.severity, "❓"
            )
            line_info = f"Line {issue.line}: " if issue.line else ""
            table.add_row(
                f"{icon} [{issue.severity}]",
                f"{line_info}{issue.message}\n   → {issue.suggestion}",
            )

        console.print(
            Panel(table, title=f"📁 {fr.file_path}", border_style="blue", padding=(1, 2))
        )

    # 总结
    summary_color = "green" if report.overall_score >= 80 else "yellow" if report.overall_score >= 60 else "red"
    console.print(
        Panel(
            f"[bold {summary_color}]总评分: {report.overall_score}/100[/bold {summary_color}]\n"
            f"扫描文件: {len(report.files)} | 发现问题: {report.total_issues}",
            title="📋 审查总结",
            border_style=summary_color,
        )
    )

# ── CLI ──────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="MiMo Code Review Agent")
    sub = parser.add_subparsers(dest="command")

    # review 子命令
    review_p = sub.add_parser("review", help="审查代码")
    review_p.add_argument("--file", "-f", help="审查单个文件")
    review_p.add_argument("--dir", "-d", help="审查整个目录")

    # pr 子命令
    pr_p = sub.add_parser("pr", help="审查 GitHub PR")
    pr_p.add_argument("--repo", required=True, help="owner/repo")
    pr_p.add_argument("--pr", type=int, required=True, help="PR 编号")

    args = parser.parse_args()

    api_key = os.environ.get("MIMO_API_KEY")
    if not api_key:
        console.print("[red]请设置 MIMO_API_KEY 环境变量[/red]")
        return

    reviewer = CodeReviewer(api_key)

    try:
        if args.command == "review":
            if args.file:
                report = ReviewReport(
                    files=[await reviewer.review_file(args.file)],
                    overall_score=0,
                    total_issues=0,
                )
                report.overall_score = report.files[0].score
                report.total_issues = len(report.files[0].issues)
            elif args.dir:
                report = await reviewer.review_directory(args.dir)
            else:
                parser.print_help()
                return

            display_report(report)

        elif args.command == "pr":
            console.print(f"[cyan]🔗 正在获取 PR: {args.repo}#{args.pr}[/cyan]")
            console.print("[yellow]GitHub PR 功能需要配置 GITHUB_TOKEN[/yellow]")

        else:
            parser.print_help()

    finally:
        await reviewer.close()


if __name__ == "__main__":
    asyncio.run(main())
