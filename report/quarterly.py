"""四半期レポート生成(差別化: 全数値に出典=集計クエリIDを自動付与).

営業転用可能な主張は「実測に基づく主張のみ」を生成し、数値には脚注(出典)を必ず付ける。
LOC等の誤誘導しやすい指標は単独提示しない。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from metrics.collector import MetricsSummary


@dataclass
class Claim:
    text: str
    value: float
    source_query_id: str      # 出典(集計クエリID)


def build_claims(summary: MetricsSummary) -> List[Claim]:
    """実測に基づく主張のみ。各主張に出典クエリIDを付与する."""
    claims = [
        Claim("AI支援PR比率", summary.ai_assisted_ratio, "Q-AI-RATIO-001"),
        Claim("AI支援PRの平均リードタイム(h)", summary.lead_time_ai, "Q-LEADTIME-AI-002"),
        Claim("非AI PRの平均リードタイム(h)", summary.lead_time_non_ai, "Q-LEADTIME-NON-003"),
        Claim("リードタイム削減率(%)", summary.lead_time_reduction_pct(), "Q-REDUCTION-004"),
        Claim("AI支援PRのリバート率", summary.revert_rate_ai, "Q-REVERT-AI-005"),
    ]
    return claims


def render_markdown(summary: MetricsSummary) -> str:
    claims = build_claims(summary)
    lines = ["# 開発生産性 四半期レポート", "",
             f"対象PR数: {summary.total_prs}", "",
             "| 指標 | 値 | 出典(集計クエリID) |", "|------|----:|------------------|"]
    for c in claims:
        val = f"{c.value:.1f}" if abs(c.value) >= 1 or c.value == 0 else f"{c.value:.3f}"
        lines.append(f"| {c.text} | {val} | `{c.source_query_id}` |")
    lines += ["",
              "> 注記: AI支援比率は単独評価せず、リードタイム・リバート率とセットで解釈すること。",
              "> LOC(行数)ベースの生産性指標は誤誘導のため掲載しない。"]
    return "\n".join(lines)


def all_numbers_have_source(summary: MetricsSummary) -> bool:
    return all(c.source_query_id for c in build_claims(summary))
