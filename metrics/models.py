"""計測対象のデータモデル(GitHub API read-onlyで取得する想定。コード本文は含めない)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Commit:
    sha: str
    message: str            # 本文＋トレーラー(コード差分は含めない)
    declared_ai: bool = False  # 開発者の申告タグ


@dataclass
class PullRequest:
    id: int
    commits: List[Commit]
    lead_time_hours: float
    review_rounds: int
    reverted: bool = False
