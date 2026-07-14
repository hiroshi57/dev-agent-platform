import React from "react";

// 四半期レポートビュー(出典クエリID付き, 営業転用可能な実測ベース主張)。
export default function QuarterlyView({ claims }) {
  return (
    <div className="card">
      <h2>四半期レポート（実測ベース・出典付き）</h2>
      <table><thead><tr><th>指標</th><th>値</th><th>出典(集計クエリID)</th></tr></thead>
        <tbody>{(claims || []).map((c) => (
          <tr key={c.source_query_id}><td>{c.text}</td><td>{c.value}</td>
            <td><code>{c.source_query_id}</code></td></tr>))}
        </tbody></table>
      <p className="note">営業資料転用時も数値の出典を明記し、実測に基づく主張のみ使用すること。</p>
    </div>
  );
}
