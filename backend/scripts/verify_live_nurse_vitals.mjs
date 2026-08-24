/** Verify the deployed Nurse Dashboard vitals API against an active Atlas visit. */
const base = (process.env.OPD_API_URL ?? "https://opd-smartqueue-api.onrender.com").replace(/\/$/, "");
const password = process.env.OPD_TEST_PASSWORD;
const email = process.env.OPD_NURSE_EMAIL ?? "nurse.kavya@opdsmartqueue.example.com";
if (!password) throw new Error("OPD_TEST_PASSWORD is required.");

async function request(path, options = {}, accessToken) {
  const url = new URL(`${base}${path}`);
  const client = await import(url.protocol === "https:" ? "node:https" : "node:http");
  return new Promise((resolve, reject) => {
    const outgoing = client.request(url, { method: options.method ?? "GET", headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) } }, (incoming) => {
      const chunks = [];
      incoming.on("data", (chunk) => chunks.push(chunk));
      incoming.on("end", () => {
        let body = null;
        try { body = JSON.parse(Buffer.concat(chunks).toString("utf8")); } catch { /* handled below */ }
        resolve({ status: incoming.statusCode ?? 0, body });
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
if (login.user.role !== "nurse") throw new Error("The supplied account is not a nurse.");
const visits = await api("/api/nurse/queue", {}, login.access_token);
const active = visits.find((visit) => ["WAITING", "CALLED", "IN_CONSULTATION"].includes(visit.status));
if (!active) throw new Error("No active visit is currently assigned to this nurse.");
const vital = await api("/api/vitals", { method: "POST", body: JSON.stringify({ token_id: active.id, temperature: 98.8, heart_rate: 76, blood_pressure: { systolic: 118, diastolic: 77 }, spo2: 99 }) }, login.access_token);
const history = await api(`/api/vitals/${active.patient_id}`, {}, login.access_token);
if (!history.some((item) => item.id === vital.id)) throw new Error("The newly recorded vital was not returned by the nurse history endpoint.");
console.log(JSON.stringify({ nurse: login.user.email, token_number: active.token_number, token_status: active.status, vital_id: vital.id, recorded_for_patient: vital.patient_id, history_count: history.length }, null, 2));
