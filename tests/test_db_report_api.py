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
