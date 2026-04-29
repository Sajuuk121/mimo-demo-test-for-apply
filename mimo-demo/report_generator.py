"""报告生成器 - 支持 Markdown / JSON / HTML 格式"""

import json
from datetime import datetime
from pathlib import Path

from code_reviewer import ReviewReport, FileReview


def to_markdown(report: ReviewReport) -> str:
    """生成 Markdown 格式报告"""
    lines = [
        f"# MiMo Code Review Report",
        f"",
        f"**日期:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**总评分:** {report.overall_score}/100",
        f"**扫描文件:** {len(report.files)}",
        f"**发现问题:** {report.total_issues}",
        f"",
        "---",
        "",
    ]

    for fr in report.files:
        score_emoji = "✅" if fr.score >= 80 else "⚠️" if fr.score >= 60 else "❌"
        lines.append(f"## {score_emoji} {fr.file_path} — {fr.score}/100")
        lines.append("")

        for issue in fr.issues:
            icon = {"HIGH": "🔴", "MED": "🟡", "LOW": "🔵", "INFO": "ℹ️"}.get(
                issue.severity, "❓"
            )
            line_info = f" (Line {issue.line})" if issue.line else ""
            lines.append(f"- {icon} **[{issue.severity}]**{line_info} {issue.message}")
            lines.append(f"  - 💡 {issue.suggestion}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def to_json(report: ReviewReport) -> str:
    """生成 JSON 格式报告"""
    return json.dumps(report.model_dump(), ensure_ascii=False, indent=2)


def save_report(report: ReviewReport, output_path: str, fmt: str = "md"):
    """保存报告到文件"""
    content = to_markdown(report) if fmt == "md" else to_json(report)
    Path(output_path).write_text(content, encoding="utf-8")
