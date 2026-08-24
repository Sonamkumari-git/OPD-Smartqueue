/** Verify real nurse-edit/delete and doctor-visible patient vitals against the deployed API. */
const base = (process.env.OPD_API_URL ?? "https://opd-smartqueue-api.onrender.com").replace(/\/$/, "");
const password = process.env.OPD_TEST_PASSWORD;
if (!password) throw new Error("OPD_TEST_PASSWORD is required.");

async function request(path, options = {}, accessToken) {
  const url = new URL(`${base}${path}`);
  const client = await import(url.protocol === "https:" ? "node:https" : "node:http");
  return new Promise((resolve, reject) => {
    const outgoing = client.request(url, { method: options.method ?? "GET", headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}) } }, (incoming) => {
      const chunks = [];
      incoming.on("data", (chunk) => chunks.push(chunk));
      incoming.on("end", () => { let body = null; try { body = JSON.parse(Buffer.concat(chunks).toString("utf8")); } catch { /* handled by status */ } resolve({ status: incoming.statusCode ?? 0, body }); });
    });
    outgoing.setTimeout(60_000, () => outgoing.destroy(new Error(`Request timed out: ${path}`)));
    outgoing.on("error", reject);
    if (options.body) outgoing.write(options.body);
    outgoing.end();
  });
}

async function api(path, options, token) {
  const result = await request(path, options, token);
  if (result.status < 200 || result.status >= 300 || !result.body?.success) throw new Error(`${path}: ${result.body?.message ?? `HTTP ${result.status}`}`);
  return result.body.data;
}
const login = (email) => api("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
const [nurse, doctor] = await Promise.all([login("nurse.kavya@opdsmartqueue.example.com"), login("dr.aarav.mehta@opdsmartqueue.example.com")]);
const visits = await api("/api/nurse/queue", {}, nurse.access_token);
const visit = visits.find((item) => item.token_number === "C-001") ?? visits.find((item) => item.status === "WAITING");
if (!visit) throw new Error("No waiting assigned visit is available for the collaboration verification.");
const created = await api("/api/vitals", { method: "POST", body: JSON.stringify({ token_id: visit.id, temperature: 98.6, heart_rate: 74, blood_pressure: { systolic: 116, diastolic: 75 }, spo2: 99 }) }, nurse.access_token);
const updated = await api(`/api/vitals/${created.id}`, { method: "PATCH", body: JSON.stringify({ temperature: 99.1, heart_rate: 80, blood_pressure: { systolic: 120, diastolic: 78 }, spo2: 98 }) }, nurse.access_token);
if (updated.heart_rate !== 80 || updated.patient_name !== visit.patient_name) throw new Error("Nurse vital update did not retain the patient-linked observation.");
const called = await api("/api/doctors/me/call-next", { method: "POST" }, doctor.access_token);
if (called.id !== visit.id) throw new Error("Doctor call-next did not select the active visit used for the nurse observation.");
await api("/api/doctors/me/start-consultation", { method: "POST", body: JSON.stringify({ token_id: visit.id }) }, doctor.access_token);
const doctorHistory = await api(`/api/vitals/${visit.patient_id}`, {}, doctor.access_token);
if (!doctorHistory.some((item) => item.id === created.id && item.patient_name === visit.patient_name && item.heart_rate === 80)) throw new Error("Assigned doctor could not see the updated patient-linked nurse observation.");
await api(`/api/vitals/${created.id}`, { method: "DELETE" }, nurse.access_token);
const nurseHistory = await api(`/api/vitals/${visit.patient_id}`, {}, nurse.access_token);
if (nurseHistory.some((item) => item.id === created.id)) throw new Error("Nurse vital delete did not remove the selected observation.");
console.log(JSON.stringify({ token_number: visit.token_number, patient_name: visit.patient_name, nurse_edit: true, doctor_visibility: true, nurse_delete: true }, null, 2));
