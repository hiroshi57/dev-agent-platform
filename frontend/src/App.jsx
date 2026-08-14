import React, { useEffect, useState } from "react";
import MetricsDashboard from "./screens/MetricsDashboard.jsx";
import QuarterlyView from "./screens/QuarterlyView.jsx";
import { summary as fetchSummary, claims as fetchClaims, openReport } from "./api.js";

// デモデータ(バックエンド未起動でも画面確認可能)。
// 以前はこの値が常時ハードコード表示され、実バックエンド(/v1/summary)には
// 一度も接続されない状態だった(api.js の summary() が未使用のdead code)。
// 現在は起動時に実データ取得を試み、失敗時のみこのデモ値にフォールバックする。
const DEMO_SUMMARY = {
  total_prs: 5, ai_assisted_ratio: 0.4, lead_time_ai: 7.0, lead_time_non_ai: 20.0,
  revert_rate_ai: 0.5, revert_rate_non_ai: 0.0, lead_time_reduction_pct: 65.0,
  ai_pr_count: 2, total_hours_saved: 26.0,
};
const DEMO_CLAIMS = [
  { text: "AI支援PR比率", value: 0.4, source_query_id: "Q-AI-RATIO-001" },
  { text: "リードタイム削減率(%)", value: 65.0, source_query_id: "Q-REDUCTION-004" },
  { text: "AI支援PRのリバート率", value: 0.5, source_query_id: "Q-REVERT-AI-005" },
  { text: "非AI PRのリバート率", value: 0.0, source_query_id: "Q-REVERT-NON-006" },
  { text: "削減工数(四半期, h)", value: 26.0, source_query_id: "Q-HOURS-SAVED-007" },
];

export default function App() {
  const [tab, setTab] = useState("metrics");
  const [tenant, setTenant] = useState("t-demo");
  const [summary, setSummary] = useState(DEMO_SUMMARY);
  const [reportClaims, setReportClaims] = useState(DEMO_CLAIMS);
  const [isLive, setIsLive] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchSummary(tenant), fetchClaims(tenant)])
      .then(([s, c]) => {
        if (cancelled) return;
        setSummary(s);
        setReportClaims(c);
        setIsLive(true);
        setError("");
      })
      .catch((e) => {
        if (cancelled) return;
        // バックエンド未起動 or 該当テナントのデータ未取込。
        // デモ値へフォールバックしつつ、ユーザーには「デモ表示中」を明示する。
        setSummary(DEMO_SUMMARY);
        setReportClaims(DEMO_CLAIMS);
        setIsLive(false);
        setError(e.message);
      });
    return () => { cancelled = true; };
  }, [tenant]);

  const handleOpenReport = async () => {
    try {
      await openReport(tenant);
    } catch (e) {
      alert(`四半期レポートの取得に失敗しました: ${e.message}`);
    }
  };

  return (
    <div className="wrap">
      <h1>開発エージェント生産性基盤</h1>
      <div className="tenant-bar">
        <label>
          テナントID:
          <input value={tenant} onChange={(e) => setTenant(e.target.value)} />
        </label>
        <span className={isLive ? "badge live" : "badge demo"}>
          {isLive ? "● 実データ表示中" : "○ デモデータ表示中(バックエンド未接続)"}
        </span>
      </div>
      {!isLive && error && (
        <p className="note" title={error}>
          ※ /v1/summary への接続に失敗したためデモ値を表示しています。
        </p>
      )}
      <nav>
        <button onClick={() => setTab("metrics")} disabled={tab === "metrics"}>計測ダッシュボード</button>
        <button onClick={() => setTab("quarterly")} disabled={tab === "quarterly"}>四半期レポート</button>
      </nav>
      {tab === "metrics"
        ? <MetricsDashboard s={summary} onOpenReport={handleOpenReport} />
        : <QuarterlyView claims={reportClaims} />}
    </div>
  );
}
