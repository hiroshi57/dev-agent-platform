# dev-agent-platform

開発エージェント生産性基盤: Claude Code等のコーディングエージェントを受託開発に安全に組み込み、
効果を**計測・証明**するための社内投資基盤。

## 差別化ポイント

1. 開発エージェント運用を**計測可能**にする（案件別のAI寄与率・削減工数を数値化）
2. その数値を**営業資料に転用**（「AI開発体制により従来比◯%短納期」を実測で主張）
3. 効率化を "やっている" ではなく **"証明できる"** 状態にする

## ステータス

🟢 **差別化コア実装済み**（AI寄与計測＋出典付きレポート＋リポジトリガード） / 拡張は承認後

- [docs/metrics_definition.md](docs/metrics_definition.md) — 測る/測らない/誤用リスクと緩和
- `metrics/` — AI寄与判定(トレーラー＋申告) + リードタイム/リバート率集計 + リポジトリガード
- `report/` — 四半期レポート(全数値に出典クエリID、LOC単独評価禁止の注記) （tests 7件PASS）
- `kit/hooks/pre-commit` — 使用不可リポジトリでのAI支援コミット警告

```bash
python demo.py          # 計測サマリ + 出典付きレポート + リポジトリガード
python -m pytest -q
```

進め方（プロンプト指定）: 計測指標定義書 → **承認** → 実装（E1標準運用キット→E2計測→E3ダッシュボード→E4ナレッジループ）。

## 予定フォルダ構成（実装時）

```
kit/{CLAUDE.md.template, review_checklist.md, prompts/, hooks/pre-commit}
metrics/{collector(GitHub API read-only), attribution, models}
dashboard/(Streamlit) / report/{quarterly, sales_claims_template}
knowledge_loop/ / tests/{test_attribution, test_repo_guard}
```
