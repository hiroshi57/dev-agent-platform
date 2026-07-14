"""開発エージェント生産性 API(FastAPI). PR取込 -> 集計 -> 四半期レポート. テナント分離.
`uvicorn service.api:app --reload`
"""
from metrics import MetricsCollector, from_export
from .db import ServiceDB
from .report_html import build_html_report

DB = ServiceDB(":memory:")
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
        if not x_tenant_id:
            raise HTTPException(401, "tenant required")
        return x_tenant_id

    class IngestIn(BaseModel):
        repo: str
        prs: list

    @app.post("/v1/ingest")
    def ingest_prs(body: IngestIn, t: str = Depends(tenant)):
        return {"ingested": ingest(t, body.repo, body.prs)}

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

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    return app


try:  # pragma: no cover
    app = create_app()
except Exception:
    app = None
