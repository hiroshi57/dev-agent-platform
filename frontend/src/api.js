const BASE = import.meta.env?.VITE_API || "http://localhost:8000";
const h = (t) => ({ "Content-Type": "application/json", "X-Tenant-Id": t });

export async function ingest(t, repo, prs) {
  return (await fetch(`${BASE}/v1/ingest`, { method: "POST", headers: h(t), body: JSON.stringify({ repo, prs }) })).json();
}
export async function summary(t) {
  return (await fetch(`${BASE}/v1/summary`, { headers: h(t) })).json();
}
export function reportUrl() { return `${BASE}/v1/report`; }
