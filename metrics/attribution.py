"""AI寄与判定. コミットトレーラー(Co-Authored-By)＋開発者申告タグの併用.

行数ベースの判定は誤誘導しやすいため用いない(metrics_definition.md 参照)。
"""
from __future__ import annotations

import re
from typing import List

from .models import Commit, PullRequest

# Co-Authored-By: ... Claude / GPT / Copilot 等
_TRAILER_RE = re.compile(r"co-authored-by:.*(claude|gpt|copilot|codex)", re.IGNORECASE)
_TAG_RE = re.compile(r"\[ai-assisted\]", re.IGNORECASE)


def is_ai_assisted_commit(commit: Commit) -> bool:
    if commit.declared_ai:
        return True
    if _TRAILER_RE.search(commit.message):
        return True
    if _TAG_RE.search(commit.message):
        return True
    return False


def is_ai_assisted_pr(pr: PullRequest) -> bool:
    return any(is_ai_assisted_commit(c) for c in pr.commits)
