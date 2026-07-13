"""E2 GitHub コレクタ. read-only エクスポート(PRメタデータ)を PullRequest に変換する.

コード本文は取得しない(メタデータのみ)。リードタイムは作成→マージのタイムスタンプから算出。
本番では GitHub API(read権限のみ)から同形式のdictを得る想定。
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from .models import Commit, PullRequest


def _parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _lead_time_hours(created_at: str, merged_at: str) -> float:
    if not created_at or not merged_at:
        return 0.0
    delta = _parse_ts(merged_at) - _parse_ts(created_at)
    return round(delta.total_seconds() / 3600, 2)


def from_export(prs_raw: List[Dict]) -> List[PullRequest]:
    """GitHub API 相当のエクスポート(dictの配列)を PullRequest に変換."""
    out: List[PullRequest] = []
    for pr in prs_raw:
        commits = [Commit(sha=c.get("sha", ""), message=c.get("message", ""),
                          declared_ai=c.get("declared_ai", False))
                   for c in pr.get("commits", [])]
        out.append(PullRequest(
            id=pr["number"],
            commits=commits,
            lead_time_hours=_lead_time_hours(pr.get("created_at", ""), pr.get("merged_at", "")),
            review_rounds=pr.get("review_rounds", 0),
            reverted=pr.get("reverted", False),
        ))
    return out
