"""永続化層(SQLite, 標準ライブラリ). PRメタデータ保存(コード本文なし). テナント分離.

注意: 「テナント分離」は SQL クエリレベルで tenant_id フィルタを強制するものであり、
呼び出し側の認証・認可(誰が名乗ったtenant_idを信じるか)は service/api.py 側の責務。
このモジュール単体では「他テナントの行が混ざらない」ことのみを保証する。
"""
from __future__ import annotations

import json
import sqlite3
import threading
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
    commits TEXT NOT NULL,
    UNIQUE(tenant_id, repo, number)
);
"""


class ServiceDB:
    def __init__(self, path: str = ":memory:") -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()
        # sqlite3 の単一コネクションは複数スレッドからの同時書き込みに弱いため
        # (FastAPI の同期エンドポイントはスレッドプールで実行される)、
        # 書き込みはロックで直列化する。
        self._write_lock = threading.Lock()

    def add_prs(self, tenant_id: str, repo: str, prs: List[PullRequest]) -> int:
        """PRを取込む。同一 (tenant_id, repo, number) は再取込に対して冪等
        (INSERT OR REPLACE で上書き)。これにより再実行・重複配信で
        計測値が水増しされることを防ぐ。"""
        with self._write_lock:
            for pr in prs:
                commits = json.dumps([{"sha": c.sha, "message": c.message, "declared_ai": c.declared_ai}
                                      for c in pr.commits], ensure_ascii=False)
                self.conn.execute(
                    "INSERT INTO pr_records(tenant_id, repo, number, lead_time_hours, review_rounds, "
                    "reverted, commits) VALUES (?,?,?,?,?,?,?) "
                    "ON CONFLICT(tenant_id, repo, number) DO UPDATE SET "
                    "lead_time_hours=excluded.lead_time_hours, "
                    "review_rounds=excluded.review_rounds, "
                    "reverted=excluded.reverted, "
                    "commits=excluded.commits",
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
