"""AI寄与の因果効果推定 + ゲーミング検知(尖った武器).

「AI支援PRはリードタイムが短い」という相関を、交絡(レビュー往復数)を調整した
回帰で因果効果に近づける。加えてトレーラー乱用(ゲーミング)を検知する。
標準ライブラリのみ(重回帰は正規方程式を2x2で解く最小実装)。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .attribution import is_ai_assisted_pr
from .models import PullRequest


@dataclass
class CausalEstimate:
    naive_diff: float          # 単純な平均差(AI - 非AI)のリードタイム
    adjusted_effect: float     # レビュー往復数で調整した後のAI係数
    n: int
    note: str = "観察データのため因果の十分条件ではない(交絡調整済みの推定値)"

    def as_dict(self):
        return {"naive_diff": round(self.naive_diff, 2),
                "adjusted_effect": round(self.adjusted_effect, 2),
                "n": self.n, "note": self.note}


def _mean(xs):
    return sum(xs) / len(xs) if xs else 0.0


def estimate_ai_effect(prs: List[PullRequest]) -> CausalEstimate:
    """lead_time ~ b0 + b1*ai + b2*review_rounds を最小二乗で解き、b1(AI効果)を返す."""
    rows = []
    for pr in prs:
        ai = 1.0 if is_ai_assisted_pr(pr) else 0.0
        rows.append((pr.lead_time_hours, ai, float(pr.review_rounds)))
    n = len(rows)
    ai_lt = [r[0] for r in rows if r[1] == 1.0]
    non_lt = [r[0] for r in rows if r[1] == 0.0]
    naive = _mean(ai_lt) - _mean(non_lt)
    if n < 3:
        return CausalEstimate(naive_diff=naive, adjusted_effect=naive, n=n)

    # 2説明変数の重回帰を正規方程式で解く(交絡=review_rounds を調整)
    y = [r[0] for r in rows]
    x1 = [r[1] for r in rows]   # ai
    x2 = [r[2] for r in rows]   # review_rounds
    adjusted = _partial_coef(y, x1, x2)
    return CausalEstimate(naive_diff=naive, adjusted_effect=adjusted, n=n)


def _partial_coef(y, x1, x2):
    """x1 を x2 で回帰して残差を取り、y の残差との単回帰係数(=x1の偏回帰係数)を返す(FWL定理)."""
    def _resid(target, ctrl):
        mc = _mean(ctrl); mt = _mean(target)
        den = sum((c - mc) ** 2 for c in ctrl) or 1.0
        b = sum((ctrl[i] - mc) * (target[i] - mt) for i in range(len(ctrl))) / den
        a = mt - b * mc
        return [target[i] - (a + b * ctrl[i]) for i in range(len(target))]
    rx = _resid(x1, x2)   # x1のうちx2で説明できない部分
    ry = _resid(y, x2)
    den = sum(v * v for v in rx) or 1.0
    return sum(rx[i] * ry[i] for i in range(len(rx))) / den


@dataclass
class GamingFlag:
    pr_id: int
    flagged: bool
    reason: str


def detect_gaming(prs: List[PullRequest]) -> List[GamingFlag]:
    """ゲーミング検知: AI寄与トレーラーがあるのにレビュー実体がない(review_rounds=0)
    かつ即マージ(短すぎるリードタイム)のPRを疑わしいとフラグする."""
    flags = []
    for pr in prs:
        if is_ai_assisted_pr(pr) and pr.review_rounds == 0 and pr.lead_time_hours < 1.0:
            flags.append(GamingFlag(pr.id, True,
                                    "AI寄与トレーラーありだがレビュー往復0かつ即マージ(<1h)"))
    return flags
