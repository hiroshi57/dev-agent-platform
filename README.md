# dev-agent-platform

開発エージェント生産性基盤: Claude Code等のコーディングエージェントを受託開発に安全に組み込み、
効果を**計測・証明**するための社内投資基盤。

## 差別化ポイント

1. 開発エージェント運用を**計測可能**にする（案件別のAI寄与率・削減工数を数値化）
2. その数値を**営業資料に転用**（「AI開発体制により従来比◯%短納期」を実測で主張）
3. 効率化を "やっている" ではなく **"証明できる"** 状態にする

## ステータス

🟢 **全機能拡張中**（E1キット / E2計測+GitHubコレクタ / E3出典レポート / E4ナレッジループ）

- [docs/metrics_definition.md](docs/metrics_definition.md) — 測る/測らない/誤用リスクと緩和
- `metrics/attribution,collector` — AI寄与判定 + リードタイム/リバート率集計
- `metrics/github_source` — E2 read-onlyエクスポート取込(コード本文なし, リードタイム算出)
- `metrics/repo_guard` + `kit/hooks/pre-commit` — 使用不可リポジトリ警告
- `report/` — 四半期レポート(全数値に出典クエリID, LOC単独評価禁止)
- `knowledge_loop/` — E4 高効果プロンプトを特定し標準キット反映issueを自動起票(**人の承認必須**)

```bash
python demo.py          # 計測サマリ + 出典付きレポート + リポジトリガード
python -m pytest -q     # テスト18件(DB/テナント分離/HTMLレポート/API E2E含む)
```

## 本番構成（SQLite + HTMLレポート + Vite 2画面）

- **DB**: `service/db.py`（SQLite）。PRメタデータ保存(コード本文なし)、全クエリ tenant_id 強制フィルタ＝**テナント分離**
- **API**: `service/api.py`（FastAPI）。ingest(PR取込) / summary / report(HTML四半期)
- **HTMLレポート**: `service/report_html.py`（全数値に出典クエリID、LOC単独評価禁止の注記）
- **フロント**: `frontend/`（React+Vite）。**計測ダッシュボード**＋**四半期レポート**の2画面。ビルド不要は `frontend/standalone.html`
- **CI**: `.github/workflows/ci.yml`

```bash
uvicorn service.api:app --reload
cd frontend && npm install && npm run dev     # or: open frontend/standalone.html
```

## 予定フォルダ構成（実装時）

```
kit/{CLAUDE.md.template, review_checklist.md, prompts/, hooks/pre-commit}
metrics/{collector(GitHub API read-only), attribution, models}
dashboard/(Streamlit) / report/{quarterly, sales_claims_template}
knowledge_loop/ / tests/{test_attribution, test_repo_guard}
```
