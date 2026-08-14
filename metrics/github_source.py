"""E2 GitHub コレクタ. read-only エクスポート(PRメタデータ)を PullRequest に変換する.

コード本文は取得しない(メタデータのみ)。リードタイムは作成→マージのタイムスタンプから算出。
本番では GitHub API(read権限のみ)から同形式のdictを得る想定。
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from .models import Commit, PullRequest


def _parse_ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _lead_time_hours(created_at: str, merged_at: str) -> Optional[float]:
    """作成→マージの経過時間(h)。未マージ(merged_at欠落)は None を返し、
    呼び出し側で「リードタイム未確定のPR」として除外できるようにする。
    (0.0を返すと「即マージ」と区別が付かず、平均値やゲーミング検知を歪めるため。)
    """
    if not created_at or not merged_at:
        return None
    delta = _parse_ts(merged_at) - _parse_ts(created_at)
    hours = delta.total_seconds() / 3600
    if hours < 0:
        # merged_at < created_at はタイムスタンプ不整合(取込元データ不良)。
        # 集計を汚さないよう、これも「リードタイム未確定」として扱う。
        return None
    return round(hours, 2)


def from_export(prs_raw: List[Dict]) -> List[PullRequest]:
    """GitHub API 相当のエクスポート(dictの配列)を PullRequest に変換.

    未マージ、またはタイムスタンプ不整合(merged_at < created_at)のPRは
    リードタイムを計測できないため、計測対象から除外する(0.0で埋めない)。
    """
    out: List[PullRequest] = []
    for pr in prs_raw:
        if "number" not in pr:
            raise ValueError(f"PRエクスポートに 'number' がありません: {pr!r}")
        lead_time = _lead_time_hours(pr.get("created_at", ""), pr.get("merged_at", ""))
        if lead_time is None:
            continue
        commits = [Commit(sha=c.get("sha", ""), message=c.get("message", ""),
                          declared_ai=c.get("declared_ai", False))
                   for c in pr.get("commits", [])]
        out.append(PullRequest(
            id=pr["number"],
            commits=commits,
            lead_time_hours=lead_time,
            review_rounds=pr.get("review_rounds", 0),
            reverted=pr.get("reverted", False),
        ))
    return out
