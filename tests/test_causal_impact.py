import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from metrics import estimate_ai_effect, detect_gaming, Commit, PullRequest  # noqa: E402

TR = "impl\n\nCo-Authored-By: Claude <x>"


def _pr(num, lead, reviews, ai, reverted=False):
    msg = TR if ai else "通常コミット"
    return PullRequest(id=num, commits=[Commit(f"c{num}", msg)],
                       lead_time_hours=lead, review_rounds=reviews, reverted=reverted)


def test_naive_diff_negative_when_ai_faster():
    prs = [_pr(1, 5, 1, True), _pr(2, 6, 1, True), _pr(3, 20, 3, False), _pr(4, 18, 3, False)]
    est = estimate_ai_effect(prs)
    assert est.naive_diff < 0        # AIの方が速い(リードタイム短い)


def test_adjusted_effect_computed():
    prs = [_pr(1, 5, 1, True), _pr(2, 6, 2, True), _pr(3, 20, 3, False),
           _pr(4, 18, 2, False), _pr(5, 10, 1, True)]
    est = estimate_ai_effect(prs)
    assert est.n == 5
    assert isinstance(est.adjusted_effect, float)
    assert "交絡" in est.note


def test_small_sample_falls_back_to_naive():
    prs = [_pr(1, 5, 1, True), _pr(2, 20, 3, False)]
    est = estimate_ai_effect(prs)
    assert est.adjusted_effect == est.naive_diff   # n<3 は単純差


def test_gaming_detection_flags_suspicious():
    prs = [_pr(1, 0.5, 0, True), _pr(2, 6, 2, True), _pr(3, 20, 3, False)]
    flags = detect_gaming(prs)
    ids = [f.pr_id for f in flags]
    assert 1 in ids                  # トレーラーあり×レビュー0×即マージ
    assert 2 not in ids and 3 not in ids


def test_gaming_no_false_positive_for_reviewed():
    prs = [_pr(1, 0.5, 2, True)]     # 即マージだがレビューあり
    assert detect_gaming(prs) == []
