"""四半期レポート HTMLビルダー(標準ライブラリのみ). 全数値に出典クエリID."""
from __future__ import annotations

import html

from metrics.collector import MetricsSummary
from report.quarterly import build_claims


def build_html_report(summary: MetricsSummary) -> str:
    rows = ""
    for c in build_claims(summary):
        val = f"{c.value:.1f}" if abs(c.value) >= 1 or c.value == 0 else f"{c.value:.3f}"
        rows += (f"<tr><td>{html.escape(c.text)}</td><td>{val}</td>"
                 f"<td><code>{html.escape(c.source_query_id)}</code></td></tr>")
    return f"""<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8">
<title>開発生産性 四半期レポート</title>
<style>body{{font-family:system-ui,sans-serif;margin:24px;color:#1a1a2e}}
h1{{color:#2b6cb0}} table{{border-collapse:collapse;margin:8px 0}}
th,td{{border:1px solid #dde;padding:6px 10px}} th{{background:#ebf2fb}}
.note{{color:#a15;font-size:13px}}</style></head><body>
<h1>開発生産性 四半期レポート</h1>
<p>対象PR数: {summary.total_prs}</p>
<table><tr><th>指標</th><th>値</th><th>出典(集計クエリID)</th></tr>{rows}</table>
<p class="note">※AI支援比率は単独評価せず、リードタイム・リバート率とセットで解釈すること。
LOC(行数)ベースの生産性指標は誤誘導のため掲載しない。</p>
</body></html>"""
