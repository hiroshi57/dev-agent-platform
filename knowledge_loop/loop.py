"""E4 ナレッジループ. 高効果のプロンプト/設定を特定し、標準キット反映用の
レビューissueを自動起票する(人が承認してマージする前提=自動マージはしない)。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class PromptRecord:
    prompt_id: str
    uses: int
    avg_lead_time_hours: float
    revert_rate: float


@dataclass
class IssueDraft:
    title: str
    body: str
    prompt_id: str
    requires_human_approval: bool = True   # 自動マージせず人の承認を要する

    def as_dict(self):
        return self.__dict__


class KnowledgeLoop:
    def __init__(self, min_uses: int = 3, max_revert_rate: float = 0.1) -> None:
        self.min_uses = min_uses
        self.max_revert_rate = max_revert_rate

    def top_prompts(self, records: List[PromptRecord]) -> List[PromptRecord]:
        """十分な使用回数 + 低リバート率のプロンプトを効果順(リードタイム短い順)に."""
        good = [r for r in records if r.uses >= self.min_uses and r.revert_rate <= self.max_revert_rate]
        good.sort(key=lambda r: r.avg_lead_time_hours)
        return good

    def draft_issues(self, records: List[PromptRecord]) -> List[IssueDraft]:
        drafts: List[IssueDraft] = []
        for r in self.top_prompts(records):
            drafts.append(IssueDraft(
                title=f"[kit反映提案] プロンプト {r.prompt_id} を標準キットに昇格",
                body=(f"使用 {r.uses} 回 / 平均リードタイム {r.avg_lead_time_hours}h / "
                      f"リバート率 {r.revert_rate:.0%}。実測に基づき標準キットへの反映を提案します。"
                      f"\n\n※このissueは人の承認を経てマージしてください(自動マージしません)。"),
                prompt_id=r.prompt_id,
            ))
        return drafts
