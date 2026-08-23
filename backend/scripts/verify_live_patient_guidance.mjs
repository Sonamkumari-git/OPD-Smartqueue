/** Verify status-aware patient guidance against an existing real Atlas token without mutating it. */
const base = (process.env.OPD_API_URL ?? "https://opd-smartqueue-api.onrender.com").replace(/\/$/, "");
const password = process.env.OPD_TEST_PASSWORD;
const email = process.env.OPD_PATIENT_EMAIL ?? "patient01@opdsmartqueue.example.com";

if (!password) throw new Error("OPD_TEST_PASSWORD is required.");

function assert(condition, message) { if (!condition) throw new Error(message); }

async function request(path, options = {}, accessToken) {
  const url = new URL(`${base}${path}`);
  const client = await import(url.protocol === "https:" ? "node:https" : "node:http");
  return new Promise((resolve, reject) => {
    const outgoing = client.request(url, { method: options.method ?? "GET", headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) } }, (incoming) => {
      const chunks = [];
      incoming.on("data", (chunk) => chunks.push(chunk));
      incoming.on("end", () => {
        try { resolve({ status: incoming.statusCode ?? 0, body: JSON.parse(Buffer.concat(chunks).toString("utf8")) }); }
        catch { reject(new Error(`Invalid JSON from ${path}`)); }
      });
    });
    outgoing.setTimeout(60_000, () => outgoing.destroy(new Error(`Request timed out: ${path}`)));
    outgoing.on("error", reject);
    if (options.body) outgoing.write(options.body);
    outgoing.end();
  });
}

async function api(path, options, accessToken) {
  const result = await request(path, options, accessToken);
  if (result.status < 200 || result.status >= 300 || !result.body?.success) throw new Error(`${path}: ${result.body?.message ?? `HTTP ${result.status}`}`);
  return result.body.data;
}

const login = await api("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
const tokens = await api("/api/patients/me/tokens", {}, login.access_token);
const active = tokens.find((token) => ["CALLED", "IN_CONSULTATION"].includes(token.status));
assert(active, "No called or in-consultation token exists for the selected patient.");
const position = await api(`/api/queue/token/${active.id}/position`, {}, login.access_token);
assert(position.patient_guidance === active.status, "Queue position did not return guidance matching the active token status.");
assert(position.estimated_wait_minutes === 0 && position.recommended_return_at === null, "A non-waiting patient still received a wait estimate or return time.");
console.log(JSON.stringify({ token_number: active.token_number, status: active.status, patient_guidance: position.patient_guidance, estimated_wait_minutes: position.estimated_wait_minutes, recommended_return_at: position.recommended_return_at, notice: position.estimate_notice }, null, 2));
