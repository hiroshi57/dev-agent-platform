"""開発エージェント生産性 API(FastAPI). PR取込 -> 集計 -> 四半期レポート. テナント分離.
`uvicorn service.api:app --reload`

注意(既知の制約・本番投入前に要対応):
- DB既定値は環境変数 DEV_AGENT_DB_PATH 未設定時 ":memory:"(プロセス再起動で全消失)。
  永続化するには DEV_AGENT_DB_PATH=/path/to/db.sqlite3 を設定すること。
- X-Tenant-Id は自己申告ヘッダであり認証ではない。DBクエリはtenant_idで厳密にフィルタする
  ("越境してデータが混ざらない")が、正しいtenant_idさえ知れば/推測できれば誰でもそのテナントの
  データを読める。実クライアントの本番運用前にAPIキー/JWT等の認証層を追加すること。
"""
import os

from dataclasses import asdict

from metrics import MetricsCollector, from_export
from .db import ServiceDB
from .report_html import build_html_report
from report import build_claims

DB = ServiceDB(os.environ.get("DEV_AGENT_DB_PATH", ":memory:"))
COLLECTOR = MetricsCollector()


def ingest(tenant: str, repo: str, prs_raw: list) -> int:
    prs = from_export(prs_raw)
    return DB.add_prs(tenant, repo, prs)


def create_app():  # pragma: no cover
    from fastapi import Depends, FastAPI, Header, HTTPException
    from fastapi.responses import HTMLResponse
    from pydantic import BaseModel

    app = FastAPI(title="Dev Agent Platform", version="1.0.0")

    def tenant(x_tenant_id: str = Header(...)) -> str:
        # 備考: ヘッダ自体が欠落している場合は Header(...) が必須指定のため
        # FastAPI が本関数に到達する前に 422 を返す。ここに来るのは
        # ヘッダは存在するが値が空文字のケースのみ。
        if not x_tenant_id:
            raise HTTPException(401, "tenant required")
        return x_tenant_id

    class IngestIn(BaseModel):
        repo: str
        prs: list

    @app.post("/v1/ingest")
    def ingest_prs(body: IngestIn, t: str = Depends(tenant)):
        try:
            return {"ingested": ingest(t, body.repo, body.prs)}
        except (ValueError, KeyError, TypeError) as e:
            # 取込データの形式不備(例: PR辞書に number が無い)は
            # 500(内部エラー)ではなく 400(不正リクエスト)として返す。
            raise HTTPException(400, f"invalid PR export data: {e}")

    @app.get("/v1/summary")
    def summary(t: str = Depends(tenant)):
        prs = DB.get_prs(t)
        if not prs:
            raise HTTPException(404, "no PRs")
        s = COLLECTOR.summarize(prs)
        return {**s.as_dict(), "lead_time_reduction_pct": round(s.lead_time_reduction_pct(), 1)}

    @app.get("/v1/report", response_class=HTMLResponse)
    def report(t: str = Depends(tenant)):
        prs = DB.get_prs(t)
        if not prs:
            raise HTTPException(404, "no PRs")
        return build_html_report(COLLECTOR.summarize(prs))

    @app.get("/v1/claims")
    def claims(t: str = Depends(tenant)):
        # フロントの四半期レポート画面(QuarterlyView)がハードコードされたデモ値
        # ではなく実データを描画できるよう、出典クエリID付きのJSON表現を提供する。
        prs = DB.get_prs(t)
        if not prs:
            raise HTTPException(404, "no PRs")
        s = COLLECTOR.summarize(prs)
        return [asdict(c) for c in build_claims(s)]

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


try:  # pragma: no cover
    app = create_app()
except Exception:
    app = None
