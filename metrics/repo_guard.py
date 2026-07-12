"""リポジトリガード. エージェント使用不可リポジトリでの使用を警告する(pre-commit相当)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GuardResult:
    allowed: bool
    warning: str = ""


class RepoGuard:
    def __init__(self, agent_allowed: bool) -> None:
        self.agent_allowed = agent_allowed

    def check(self, commit_is_ai_assisted: bool) -> GuardResult:
        if commit_is_ai_assisted and not self.agent_allowed:
            return GuardResult(
                allowed=False,
                warning="このリポジトリはエージェント使用不可に設定されています。"
                        "クライアントコードの取り扱い区分を確認してください。",
            )
        return GuardResult(allowed=True)
