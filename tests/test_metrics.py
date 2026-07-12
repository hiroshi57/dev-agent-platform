import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import (  # noqa: E402
    Commit, PullRequest, MetricsCollector, RepoGuard,
    is_ai_assisted_commit, is_ai_assisted_pr,
)
from report import render_markdown, build_claims, all_numbers_have_source  # noqa: E402


def test_attribution_via_trailer():
    c = Commit("x", "fix bug\n\nCo-Authored-By: Claude <noreply@anthropic.com>")
    assert is_ai_assisted_commit(c) is True


def test_attribution_via_declared_tag_and_marker():
    assert is_ai_assisted_commit(Commit("x", "impl", declared_ai=True)) is True
    assert is_ai_assisted_commit(Commit("y", "作業 [ai-assisted]")) is True
    assert is_ai_assisted_commit(Commit("z", "通常コミット")) is False


def _prs():
    tr = "impl\n\nCo-Authored-By: Claude <x>"
    return [
        PullRequest(1, [Commit("a", tr)], lead_time_hours=6, review_rounds=1),
        PullRequest(2, [Commit("b", tr)], lead_time_hours=10, review_rounds=2, reverted=True),
        PullRequest(3, [Commit("c", "通常")], lead_time_hours=20, review_rounds=3),
        PullRequest(4, [Commit("d", "通常")], lead_time_hours=16, review_rounds=2),
    ]


def test_lead_time_comparison_and_ratio():
    s = MetricsCollector().summarize(_prs())
    assert s.total_prs == 4
    assert s.ai_assisted_ratio == 0.5
    assert s.lead_time_ai < s.lead_time_non_ai       # AI支援が短い
    assert s.lead_time_reduction_pct() > 0


def test_revert_rate_split():
    s = MetricsCollector().summarize(_prs())
    assert s.revert_rate_ai == 0.5                   # AI PR 2件中1件revert
    assert s.revert_rate_non_ai == 0.0


def test_repo_guard_blocks_forbidden_repo():
    assert RepoGuard(agent_allowed=False).check(True).allowed is False
    assert RepoGuard(agent_allowed=False).check(False).allowed is True   # 非AIは許可
    assert RepoGuard(agent_allowed=True).check(True).allowed is True


def test_report_all_numbers_have_source():
    s = MetricsCollector().summarize(_prs())
    assert all_numbers_have_source(s) is True
    for c in build_claims(s):
        assert c.source_query_id.startswith("Q-")


def test_report_markdown_has_disclaimer():
    s = MetricsCollector().summarize(_prs())
    md = render_markdown(s)
    assert "出典" in md
    assert "LOC" in md                               # 単独評価禁止の注記
    assert "セットで解釈" in md
