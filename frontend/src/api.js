const BASE = import.meta.env?.VITE_API || "http://localhost:8000";
const h = (t) => ({ "Content-Type": "application/json", "X-Tenant-Id": t });

async function _asJson(res) {
  // レスポンスが2xxでない場合、本文がJSON({"detail": "..."})であっても
  // 呼び出し側に「成功データ」として渡さず、明示的にエラーとして投げる。
  // (これを怠ると画面側が s.ai_assisted_ratio 等をundefinedとして扱い、
  //  NaN%のような壊れた表示になってしまう。)
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* 本文がJSONでない場合はstatusTextのままにする */
    }
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json();
}

export async function ingest(t, repo, prs) {
  const res = await fetch(`${BASE}/v1/ingest`, {
    method: "POST",
    headers: h(t),
    body: JSON.stringify({ repo, prs }),
  });
  return _asJson(res);
}

export async function summary(t) {
  const res = await fetch(`${BASE}/v1/summary`, { headers: h(t) });
  return _asJson(res);
}

export async function claims(t) {
  const res = await fetch(`${BASE}/v1/claims`, { headers: h(t) });
  return _asJson(res);
}

// 四半期HTMLレポートを開く。
// 注意: window.open(url) によるプレーンなナビゲーションではカスタムヘッダ
// (X-Tenant-Id)を送信できないため、以前の reportUrl()+window.open() 方式では
// 本番のヘッダ必須APIに対して常に401/422で失敗していた。
// fetchでヘッダ付き取得し、Blob URLとして新規タブに開く。
export async function openReport(t) {
  const res = await fetch(`${BASE}/v1/report`, { headers: h(t) });
  if (!res.ok) {
    throw new Error(`API error ${res.status}: レポート取得に失敗しました`);
  }
  const htmlText = await res.text();
  const blobUrl = URL.createObjectURL(new Blob([htmlText], { type: "text/html" }));
  window.open(blobUrl, "_blank");
}
