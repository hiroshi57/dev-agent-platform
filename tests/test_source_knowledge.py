import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import from_export, MetricsCollector, is_ai_assisted_pr  # noqa: E402
from knowledge_loop import KnowledgeLoop, PromptRecord  # noqa: E402


# --- E2 GitHub コレクタ ---
EXPORT = [
    {"number": 1, "created_at": "2026-07-01T09:00:00Z", "merged_at": "2026-07-01T15:00:00Z",
     "review_rounds": 1, "reverted": False,
     "commits": [{"sha": "a", "message": "impl\n\nCo-Authored-By: Claude <x>"}]},
    {"number": 2, "created_at": "2026-07-02T09:00:00Z", "merged_at": "2026-07-03T09:00:00Z",
     "review_rounds": 3, "reverted": True,
     "commits": [{"sha": "b", "message": "通常コミット"}]},
]


def test_from_export_builds_prs_with_lead_time():
    prs = from_export(EXPORT)
    assert len(prs) == 2
    assert prs[0].lead_time_hours == 6.0        # 09:00->15:00
    assert prs[1].lead_time_hours == 24.0


def test_from_export_preserves_attribution():
    prs = from_export(EXPORT)
    assert is_ai_assisted_pr(prs[0]) is True     # トレーラーあり
    assert is_ai_assisted_pr(prs[1]) is False


def test_from_export_feeds_collector():
    summary = MetricsCollector().summarize(from_export(EXPORT))
    assert summary.total_prs == 2
    assert summary.ai_assisted_ratio == 0.5


# --- E4 ナレッジループ ---
def _records():
    return [
        PromptRecord("P-feature", uses=10, avg_lead_time_hours=5.0, revert_rate=0.05),
        PromptRecord("P-bugfix", uses=8, avg_lead_time_hours=8.0, revert_rate=0.0),
        PromptRecord("P-rare", uses=1, avg_lead_time_hours=3.0, revert_rate=0.0),      # 使用少
        PromptRecord("P-risky", uses=10, avg_lead_time_hours=4.0, revert_rate=0.4),    # 高revert
    ]


def test_top_prompts_filters_low_use_and_high_revert():
    top = KnowledgeLoop().top_prompts(_records())
    ids = [r.prompt_id for r in top]
    assert "P-rare" not in ids       # 使用回数不足
    assert "P-risky" not in ids      # リバート率高
    assert ids[0] == "P-feature"     # 効果順(リードタイム短い)


def test_draft_issues_require_human_approval():
    drafts = KnowledgeLoop().draft_issues(_records())
    assert drafts
    for d in drafts:
        assert d.requires_human_approval is True     # 自動マージしない
        assert d.prompt_id in {"P-feature", "P-bugfix"}
        assert "承認" in d.body


def test_no_qualifying_prompts_yields_no_issues():
    poor = [PromptRecord("x", uses=1, avg_lead_time_hours=5, revert_rate=0.9)]
    assert KnowledgeLoop().draft_issues(poor) == []
