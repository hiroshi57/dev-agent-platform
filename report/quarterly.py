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
    # 単位種別。値のフォーマットが単位によって全く違う意味を持つため明示する
    # ("ratio"の0.5と"percent"の0.5(=0.5%)は50倍違うので混同すると読み違いを招く)。
    unit: str = "number"       # "ratio" | "percent" | "hours" | "number"

    def display_value(self) -> str:
        """人間向け表示文字列(単位付き)を返す。以前は単位を付けずに生の数値
        (例: 比率0.5を"0.500"のまま)を表示しており、%表記の指標と並べたときに
        誤読を招くリスクがあった。"""
        if self.unit == "ratio":
            return f"{self.value * 100:.1f}%"
        if self.unit == "percent":
            return f"{self.value:.1f}%"
        if self.unit == "hours":
            return f"{self.value:.1f}h"
        return f"{self.value:.1f}" if abs(self.value) >= 1 or self.value == 0 else f"{self.value:.3f}"


def build_claims(summary: MetricsSummary) -> List[Claim]:
    """実測に基づく主張のみ。各主張に出典クエリIDを付与する."""
    claims = [
        Claim("AI支援PR比率", summary.ai_assisted_ratio, "Q-AI-RATIO-001", unit="ratio"),
        Claim("AI支援PRの平均リードタイム(h)", summary.lead_time_ai, "Q-LEADTIME-AI-002", unit="hours"),
        Claim("非AI PRの平均リードタイム(h)", summary.lead_time_non_ai, "Q-LEADTIME-NON-003", unit="hours"),
        Claim("リードタイム削減率(%)", summary.lead_time_reduction_pct(), "Q-REDUCTION-004", unit="percent"),
        Claim("AI支援PRのリバート率", summary.revert_rate_ai, "Q-REVERT-AI-005", unit="ratio"),
        # リバート率は単独評価を禁止しているため、必ず非AI側の値もセットで開示する。
        Claim("非AI PRのリバート率", summary.revert_rate_non_ai, "Q-REVERT-NON-006", unit="ratio"),
        # docs/metrics_definition.md で定義された「削減工数(四半期)」の実測値。
        Claim("削減工数(四半期, h)", summary.total_hours_saved, "Q-HOURS-SAVED-007", unit="hours"),
    ]
    return claims


def render_markdown(summary: MetricsSummary) -> str:
    claims = build_claims(summary)
    lines = ["# 開発生産性 四半期レポート", "",
             f"対象PR数: {summary.total_prs}", "",
             "| 指標 | 値 | 出典(集計クエリID) |", "|------|----:|------------------|"]
    for c in claims:
        lines.append(f"| {c.text} | {c.display_value()} | `{c.source_query_id}` |")
    lines += ["",
              "> 注記: AI支援比率は単独評価せず、リードタイム・リバート率とセットで解釈すること。",
              "> LOC(行数)ベースの生産性指標は誤誘導のため掲載しない。"]
    return "\n".join(lines)


def all_numbers_have_source(summary: MetricsSummary) -> bool:
    return all(c.source_query_id for c in build_claims(summary))
