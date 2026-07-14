import React from "react";

// 計測ダッシュボード: AI支援比率/リードタイム/リバート率。
export default function MetricsDashboard({ s, onOpenReport }) {
  if (!s) return <div className="card">データがありません。</div>;
  return (
    <div className="card">
      <h2>開発生産性 計測サマリ</h2>
      <div className="metrics">
        <div className="metric"><div className="label">AI支援PR比率</div>
          <div className="val">{Math.round(s.ai_assisted_ratio * 100)}%</div></div>
        <div className="metric"><div className="label">リードタイム削減</div>
          <div className="val">{s.lead_time_reduction_pct}%</div></div>
        <div className="metric"><div className="label">リバート率(AI)</div>
          <div className="val">{Math.round(s.revert_rate_ai * 100)}%</div></div>
      </div>
      <table><thead><tr><th></th><th>AI支援</th><th>非AI</th></tr></thead>
        <tbody>
          <tr><td>平均リードタイム(h)</td><td>{s.lead_time_ai}</td><td>{s.lead_time_non_ai}</td></tr>
          <tr><td>リバート率</td><td>{s.revert_rate_ai}</td><td>{s.revert_rate_non_ai}</td></tr>
        </tbody></table>
      <p className="note">※AI支援比率は単独評価せず、リードタイム・リバート率とセットで解釈。LOCは非掲載。</p>
      {onOpenReport && <button className="primary" onClick={onOpenReport}>四半期HTMLレポート</button>}
    </div>
  );
}
