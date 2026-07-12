"""計測パイプライン. PR群から AI支援比率 / リードタイム / リバート率を集計.

単独指標での評価を避けるため、AI支援比率は必ずリードタイム・リバート率とセットで返す。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .attribution import is_ai_assisted_pr
from .models import PullRequest


def _mean(xs: List[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


@dataclass
class MetricsSummary:
    total_prs: int
    ai_assisted_ratio: float
    lead_time_ai: float
    lead_time_non_ai: float
    revert_rate_ai: float
    revert_rate_non_ai: float

    def as_dict(self):
        return {k: (round(v, 3) if isinstance(v, float) else v) for k, v in self.__dict__.items()}

    def lead_time_reduction_pct(self) -> float:
        if self.lead_time_non_ai == 0:
            return 0.0
        return (self.lead_time_non_ai - self.lead_time_ai) / self.lead_time_non_ai * 100


class MetricsCollector:
    def summarize(self, prs: List[PullRequest]) -> MetricsSummary:
        ai = [p for p in prs if is_ai_assisted_pr(p)]
        non = [p for p in prs if not is_ai_assisted_pr(p)]
        n = len(prs)
        return MetricsSummary(
            total_prs=n,
            ai_assisted_ratio=(len(ai) / n if n else 0.0),
            lead_time_ai=_mean([p.lead_time_hours for p in ai]),
            lead_time_non_ai=_mean([p.lead_time_hours for p in non]),
            revert_rate_ai=(sum(1 for p in ai if p.reverted) / len(ai) if ai else 0.0),
            revert_rate_non_ai=(sum(1 for p in non if p.reverted) / len(non) if non else 0.0),
        )
