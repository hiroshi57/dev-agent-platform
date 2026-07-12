"""デモ(APIキー不要). AI寄与計測 -> レポート -> リポジトリガード. `python demo.py`"""
from metrics import Commit, PullRequest, MetricsCollector, RepoGuard, is_ai_assisted_pr
from report import render_markdown


def _sample_prs():
    ai_trailer = "実装\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
    return [
        PullRequest(1, [Commit("a1", ai_trailer)], lead_time_hours=6, review_rounds=1),
        PullRequest(2, [Commit("b1", ai_trailer)], lead_time_hours=8, review_rounds=2, reverted=True),
        PullRequest(3, [Commit("c1", "通常コミット")], lead_time_hours=20, review_rounds=3),
        PullRequest(4, [Commit("d1", "通常コミット")], lead_time_hours=16, review_rounds=2),
        PullRequest(5, [Commit("e1", "手動対応", declared_ai=False)], lead_time_hours=24, review_rounds=4),
    ]


def main():
    prs = _sample_prs()
    summary = MetricsCollector().summarize(prs)

    print("=== 計測サマリ ===")
    print(f"  AI支援PR比率: {summary.ai_assisted_ratio:.0%}")
    print(f"  リードタイム: AI={summary.lead_time_ai:.1f}h / 非AI={summary.lead_time_non_ai:.1f}h "
          f"(削減 {summary.lead_time_reduction_pct():.0f}%)")
    print(f"  リバート率: AI={summary.revert_rate_ai:.0%} / 非AI={summary.revert_rate_non_ai:.0%}")

    print("\n=== 四半期レポート(全数値に出典) ===")
    print(render_markdown(summary))

    print("\n=== リポジトリガード ===")
    guard = RepoGuard(agent_allowed=False)
    r = guard.check(commit_is_ai_assisted=True)
    print(f"  使用不可リポジトリでAI支援コミット: allowed={r.allowed} / {r.warning}")


if __name__ == "__main__":
    main()
