import React, { useState } from "react";
import MetricsDashboard from "./screens/MetricsDashboard.jsx";
import QuarterlyView from "./screens/QuarterlyView.jsx";
import { reportUrl } from "./api.js";

// デモデータ(バックエンド未起動でも画面確認可能)
const DEMO_SUMMARY = {
  total_prs: 5, ai_assisted_ratio: 0.4, lead_time_ai: 7.0, lead_time_non_ai: 20.0,
  revert_rate_ai: 0.5, revert_rate_non_ai: 0.0, lead_time_reduction_pct: 65.0,
};
const DEMO_CLAIMS = [
  { text: "AI支援PR比率", value: 0.4, source_query_id: "Q-AI-RATIO-001" },
  { text: "リードタイム削減率(%)", value: 65.0, source_query_id: "Q-REDUCTION-004" },
  { text: "AI支援PRのリバート率", value: 0.5, source_query_id: "Q-REVERT-AI-005" },
];

export default function App() {
  const [tab, setTab] = useState("metrics");
  return (
    <div className="wrap">
      <h1>開発エージェント生産性基盤</h1>
      <nav>
        <button onClick={() => setTab("metrics")} disabled={tab === "metrics"}>計測ダッシュボード</button>
        <button onClick={() => setTab("quarterly")} disabled={tab === "quarterly"}>四半期レポート</button>
      </nav>
      {tab === "metrics"
        ? <MetricsDashboard s={DEMO_SUMMARY} onOpenReport={() => window.open(reportUrl(), "_blank")} />
        : <QuarterlyView claims={DEMO_CLAIMS} />}
    </div>
  );
}
