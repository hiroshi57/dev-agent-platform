"""永続化層(SQLite, 標準ライブラリ). PRメタデータ保存(コード本文なし). テナント分離."""
from __future__ import annotations

import json
import sqlite3
from typing import Dict, List, Optional

from metrics.models import Commit, PullRequest

SCHEMA = """
CREATE TABLE IF NOT EXISTS pr_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id TEXT NOT NULL,
    repo TEXT NOT NULL,
    number INTEGER NOT NULL,
    lead_time_hours REAL NOT NULL,
    review_rounds INTEGER NOT NULL,
    reverted INTEGER NOT NULL,
    commits TEXT NOT NULL
);
"""


class ServiceDB:
    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def add_prs(self, tenant_id: str, repo: str, prs: List[PullRequest]) -> int:
        for pr in prs:
            commits = json.dumps([{"sha": c.sha, "message": c.message, "declared_ai": c.declared_ai}
                                  for c in pr.commits], ensure_ascii=False)
            self.conn.execute(
                "INSERT INTO pr_records(tenant_id, repo, number, lead_time_hours, review_rounds, "
                "reverted, commits) VALUES (?,?,?,?,?,?,?)",
                (tenant_id, repo, pr.id, pr.lead_time_hours, pr.review_rounds,
                 1 if pr.reverted else 0, commits))
        self.conn.commit()
        return len(prs)

    def get_prs(self, tenant_id: str, repo: Optional[str] = None) -> List[PullRequest]:
        if repo:
            rows = self.conn.execute(
                "SELECT * FROM pr_records WHERE tenant_id=? AND repo=?", (tenant_id, repo)).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM pr_records WHERE tenant_id=?", (tenant_id,)).fetchall()
        out = []
        for r in rows:
            commits = [Commit(**c) for c in json.loads(r["commits"])]
            out.append(PullRequest(id=r["number"], commits=commits,
                                   lead_time_hours=r["lead_time_hours"],
                                   review_rounds=r["review_rounds"], reverted=bool(r["reverted"])))
        return out

    def close(self) -> None:
        self.conn.close()
