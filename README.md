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
python -m pytest -q     # テスト31件(DB冪等性/テナント分離/HTMLレポート/API E2E/未マージPR除外 等)
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

## 既知の制約(本番の実クライアントデータで使う前に要対応)

営業資料に転用する数値の信頼性に直結するため、以下は誇張せず明記する。

- **テナント分離は認証ではない**: `X-Tenant-Id` は自己申告ヘッダで、SQLクエリはこの値で厳密に
  フィルタするが、正しい値さえ分かれば誰でもそのテナントのデータを読める。実クライアント運用前に
  APIキー/JWT等の認証層が必要([service/api.py](service/api.py) 冒頭コメント参照)。
- **AI寄与判定は自己申告ベース**: コミットトレーラー(`Co-Authored-By: Claude`等)や申告タグは
  開発者が自由に書ける文字列であり、実際にAIエージェントが使われたことを検証する仕組みはない
  (過大申告・過小申告のどちらも技術的に容易)。「Claude」はフランス語圏で一般的な人名でもあり、
  人間の共著者を誤ってAI支援と判定する可能性がある。
- **`knowledge_loop` の「自動起票」は起票を含まない**: `KnowledgeLoop.draft_issues()` は
  issue本文をPythonオブジェクトとして生成するのみで、GitHub Issues APIへの実際の書き込みは
  実装されていない。
- **出典クエリID(`Q-AI-RATIO-001`等)は静的ラベル**: 実行時刻・テナント・データセットに紐づく
  実クエリの実行ログではなく、`report/quarterly.py` に固定文字列として定義されている。
  同じ値は毎回同じIDになるため、「どの取込データから算出したか」の追跡には使えない。
  監査証跡として使うには、テナント/期間/データスナップショットIDを含む形へ拡張が必要。
- **DB既定はメモリ内**: `service/api.py` は環境変数 `DEV_AGENT_DB_PATH` 未設定時
  `:memory:` で起動し、プロセス再起動で全データが消える。永続化するにはパスを指定すること。
- **`frontend/standalone.html` は別ツール**: 「ビルド不要版」と説明しているが、実際は
  `service/api.py`・`metrics/` パッケージと接続しない独立実装(ローカルストレージ保存の
  手入力ツール)。同じ「AI有無の比較」ロジックが Python(`metrics/collector.py`)・
  React(`frontend/src/`)・standalone.html 内インラインJSの3箇所に分かれて存在し、
  用語(リードタイム/かかった日数)や判定基準がそれぞれ独自実装のため、将来的な仕様変更時に
  3箇所の同期が必要になる。
