"""GitHub PR 集成 - 自动审查 Pull Request"""

import os
from dataclasses import dataclass
from typing import Optional

import httpx


@dataclass
class PRFile:
    filename: str
    patch: str
    status: str  # added / modified / removed


class GitHubIntegration:
    """GitHub API 集成，用于获取 PR diff 并提交审查评论"""

    API_BASE = "https://api.github.com"

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.environ.get("GITHUB_TOKEN")
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
            },
            timeout=30,
        )

    async def get_pr_files(self, repo: str, pr_number: int) -> list[PRFile]:
        """获取 PR 中修改的文件"""
        resp = await self.client.get(
            f"{self.API_BASE}/repos/{repo}/pulls/{pr_number}/files"
        )
        resp.raise_for_status()
        return [
            PRFile(
                filename=f["filename"],
                patch=f.get("patch", ""),
                status=f["status"],
            )
            for f in resp.json()
        ]

    async def post_review_comment(
        self, repo: str, pr_number: int, body: str, commit_id: str
    ):
        """提交 PR 审查评论"""
        await self.client.post(
            f"{self.API_BASE}/repos/{repo}/pulls/{pr_number}/reviews",
            json={
                "commit_id": commit_id,
                "body": body,
                "event": "COMMENT",
            },
        )

    async def close(self):
        await self.client.aclose()
