import React from "react";

const pct = (v) => (typeof v === "number" && !Number.isNaN(v) ? `${Math.round(v * 100)}%` : "-");

// 計測ダッシュボード: AI支援比率/リードタイム/リバート率。
export default function MetricsDashboard({ s, onOpenReport }) {
  // APIがエラー応答({"detail": "..."})を返した場合、total_prs等の必須フィールドが
  // 欠落する。undefinedをそのままMath.round()等に渡すと"NaN%"表示になってしまうため、
  // 必須フィールドの型を明示的に検査してから描画する。
  const isValidSummary = s && typeof s.ai_assisted_ratio === "number";
  if (!isValidSummary) return <div className="card">データがありません。</div>;
  return (
    <div className="card">
      <h2>開発生産性 計測サマリ</h2>
      <div className="metrics">
        <div className="metric"><div className="label">AI支援PR比率</div>
          <div className="val">{pct(s.ai_assisted_ratio)}</div></div>
        <div className="metric"><div className="label">リードタイム削減</div>
          <div className="val">{s.lead_time_reduction_pct}%</div></div>
        <div className="metric"><div className="label">リバート率(AI)</div>
          <div className="val">{pct(s.revert_rate_ai)}</div></div>
        <div className="metric"><div className="label">削減工数(四半期)</div>
          <div className="val">{s.total_hours_saved ?? 0}h</div></div>
      </div>
      <table><thead><tr><th></th><th>AI支援</th><th>非AI</th></tr></thead>
        <tbody>
          <tr><td>平均リードタイム(h)</td><td>{s.lead_time_ai}</td><td>{s.lead_time_non_ai}</td></tr>
          {/* リバート率は割合(0-1)を%表示に統一する。以前はここだけ生の小数(例: 0.5)を
              表示しており、上のカード表示(50%)と単位が食い違っていた。 */}
          <tr><td>リバート率</td><td>{pct(s.revert_rate_ai)}</td><td>{pct(s.revert_rate_non_ai)}</td></tr>
        </tbody></table>
      <p className="note">※AI支援比率は単独評価せず、リードタイム・リバート率とセットで解釈。LOCは非掲載。</p>
      {onOpenReport && <button className="primary" onClick={onOpenReport}>四半期HTMLレポート</button>}
    </div>
  );
}
