import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from service.db import ServiceDB  # noqa: E402
from service.report_html import build_html_report  # noqa: E402
from metrics import from_export, MetricsCollector  # noqa: E402

EXPORT = [
    {"number": 1, "created_at": "2026-07-01T09:00:00Z", "merged_at": "2026-07-01T15:00:00Z",
     "review_rounds": 1, "reverted": False,
     "commits": [{"sha": "a", "message": "impl\n\nCo-Authored-By: Claude <x>"}]},
    {"number": 2, "created_at": "2026-07-02T09:00:00Z", "merged_at": "2026-07-03T09:00:00Z",
     "review_rounds": 3, "reverted": True, "commits": [{"sha": "b", "message": "通常"}]},
]


def test_pr_roundtrip_preserves_attribution():
    db = ServiceDB(":memory:")
    db.add_prs("t-a", "repoX", from_export(EXPORT))
    prs = db.get_prs("t-a")
    assert len(prs) == 2
    assert prs[0].lead_time_hours == 6.0
    assert prs[1].reverted is True


def test_tenant_isolation():
    db = ServiceDB(":memory:")
    db.add_prs("t-a", "repoX", from_export(EXPORT))
    assert db.get_prs("t-b") == []       # 越境不可


def test_html_report_has_sources_and_disclaimer():
    prs = from_export(EXPORT)
    html = build_html_report(MetricsCollector().summarize(prs))
    assert "四半期レポート" in html
    assert "Q-AI-RATIO-001" in html      # 出典クエリID
    assert "LOC" in html                 # 単独評価禁止の注記


def test_html_report_escapes():
    from metrics.collector import MetricsSummary
    s = MetricsSummary(0, 0, 0, 0, 0, 0)
    assert "<html" in build_html_report(s)


def test_api_e2e_and_tenant_isolation():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from service.api import create_app
    c = TestClient(create_app())
    ha, hb = {"X-Tenant-Id": "t-a"}, {"X-Tenant-Id": "t-b"}
    assert c.post("/v1/ingest", json={"repo": "repoX", "prs": EXPORT}, headers=ha).json()["ingested"] == 2
    assert c.get("/v1/summary", headers=hb).status_code == 404   # 越境不可(未取込)
    s = c.get("/v1/summary", headers=ha).json()
    assert s["total_prs"] == 2 and s["ai_assisted_ratio"] == 0.5
    r = c.get("/v1/report", headers=ha)
    assert r.status_code == 200 and "四半期レポート" in r.text


def test_api_ingest_rejects_malformed_pr_with_400():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient
    from service.api import create_app
    c = TestClient(create_app())
    bad = [{"created_at": "2026-07-01T09:00:00Z", "merged_at": "2026-07-01T15:00:00Z"}]  # number欠落
    r = c.post("/v1/ingest", json={"repo": "repoX", "prs": bad}, headers={"X-Tenant-Id": "t-bad"})
    assert r.status_code == 400


def test_reingest_same_pr_is_idempotent_not_duplicated():
    """同じ(tenant, repo, number)を2回取込んでも件数が倍増しないこと(再実行安全性)."""
    db = ServiceDB(":memory:")
    db.add_prs("t-a", "repoX", from_export(EXPORT))
    db.add_prs("t-a", "repoX", from_export(EXPORT))   # 再取込(例: リトライ/日次バッチの重複)
    prs = db.get_prs("t-a")
    assert len(prs) == 2   # 4件に水増しされない


def test_reingest_updates_changed_fields():
    """再取込時は最新の値で上書きされること(例: レビュー往復数の更新)."""
    db = ServiceDB(":memory:")
    db.add_prs("t-a", "repoX", from_export(EXPORT))
    updated = [dict(EXPORT[0], review_rounds=9)]
    db.add_prs("t-a", "repoX", from_export(updated))
    prs = {p.id: p for p in db.get_prs("t-a")}
    assert prs[1].review_rounds == 9
