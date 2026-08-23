/**
 * Verify real OPD SmartQueue workflows against a seeded API/database environment.
 *
 * Required environment variables:
 *   OPD_API_URL=http://127.0.0.1:8001  (or the deployed API URL)
 *   OPD_TEST_PASSWORD=<the password passed to seed_atlas_data.py>
 */

const base = (process.env.OPD_API_URL ?? "http://127.0.0.1:8001").replace(/\/$/, "");
const password = process.env.OPD_TEST_PASSWORD;
const domain = "opdsmartqueue.example.com";
const requestTimeoutMs = 60_000;

if (!password || password.length < 8) throw new Error("OPD_TEST_PASSWORD must contain the seed-account password.");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function request(path, options = {}, accessToken) {
  const url = new URL(`${base}${path}`);
  const client = await import(url.protocol === "https:" ? "node:https" : "node:http");
  const headers = {
    "Content-Type": "application/json",
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...(options.headers ?? {}),
  };
  return new Promise((resolve, reject) => {
    const outgoing = client.request(url, { method: options.method ?? "GET", headers }, (incoming) => {
      const chunks = [];
      incoming.on("data", (chunk) => chunks.push(chunk));
      incoming.on("end", () => {
        const text = Buffer.concat(chunks).toString("utf8");
        let body = null;
        try { body = JSON.parse(text); } catch { /* surfaced by status/error assertion below */ }
        resolve({ response: { status: incoming.statusCode ?? 0, ok: (incoming.statusCode ?? 0) >= 200 && (incoming.statusCode ?? 0) < 300 }, body });
      });
    });
    outgoing.setTimeout(requestTimeoutMs, () => outgoing.destroy(new Error(`Request timed out after ${requestTimeoutMs}ms: ${path}`)));
    outgoing.on("error", reject);
    if (options.body) outgoing.write(options.body);
    outgoing.end();
  });
}

async function api(path, options = {}, accessToken) {
  const { response, body } = await request(path, options, accessToken);
  if (!response.ok || !body?.success) throw new Error(`${path}: ${body?.message ?? `HTTP ${response.status}`}`);
  return body.data;
}

async function login(localPart) {
  return api("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email: `${localPart}@${domain}`, password }),
  });
}

function waitForEvent(socket, eventName, timeoutMs = 10_000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Timed out waiting for WebSocket event ${eventName}.`)), timeoutMs);
    socket.addEventListener("message", ({ data }) => {
      const event = JSON.parse(data);
      if (event.event === eventName) {
        clearTimeout(timer);
        resolve(event);
      }
    });
    socket.addEventListener("error", () => {
      clearTimeout(timer);
      reject(new Error("The authenticated WebSocket connection failed."));
    }, { once: true });
  });
}

const health = (await request("/health")).body;
const ready = (await request("/ready")).body;
assert(health?.success && health.data?.database_ready, "Health endpoint did not report a ready MongoDB connection.");
assert(ready?.success && ready.data?.ready, "Readiness endpoint did not report a ready service.");

const [admin, doctor, nurse, currentPatient, nextPatient, patientForSocket] = await Promise.all([
  login("admin"), login("dr.aarav.mehta"), login("nurse.kavya"), login("patient01"), login("patient02"), login("patient07"),
]);
assert(admin.user.role === "admin" && doctor.user.role === "doctor" && nurse.user.role === "nurse" && currentPatient.user.role === "patient", "Seeded account roles do not match expected access levels.");

const departments = await api("/api/departments");
const cardiology = departments.find((item) => item.code === "C");
const ent = departments.find((item) => item.code === "E");
assert(cardiology && ent, "Expected Cardiology and ENT departments were not returned from MongoDB.");

const [cardiologyDoctors, entDoctors, doctorQueue, nurseQueue, patientTokens] = await Promise.all([
  api(`/api/doctors?department_id=${cardiology.id}`),
  api(`/api/doctors?department_id=${ent.id}`),
  api("/api/doctors/me/queue", {}, doctor.access_token),
  api("/api/nurse/queue", {}, nurse.access_token),
  api("/api/patients/me/tokens", {}, currentPatient.access_token),
]);
assert(cardiologyDoctors.length > 0 && entDoctors.length > 0, "Seeded clinician records were not returned by catalog APIs.");
assert(doctorQueue.length >= 3 && nurseQueue.length >= 3, "Seeded queue records were not returned by doctor/nurse APIs.");

const unauthorizedAnalytics = await request("/api/analytics/overview", {}, currentPatient.access_token);
assert(unauthorizedAnalytics.response.status === 403, "Patient access unexpectedly reached administrator analytics.");

const inConsultation = patientTokens.find((item) => item.status === "IN_CONSULTATION");
assert(inConsultation, "The current seeded cardiology patient was not in consultation.");
const consultationPosition = await api(`/api/queue/token/${inConsultation.id}/position`, {}, currentPatient.access_token);
assert(consultationPosition.patient_guidance === "IN_CONSULTATION" && consultationPosition.estimated_wait_minutes === 0 && consultationPosition.recommended_return_at === null, "In-consultation patient position still exposes a waiting estimate.");
await api("/api/doctors/me/complete-consultation", { method: "POST", body: JSON.stringify({ token_id: inConsultation.id }) }, doctor.access_token);

const called = await api("/api/doctors/me/call-next", { method: "POST" }, doctor.access_token);
assert(called.status === "CALLED", "Doctor call-next did not claim the next real waiting token.");
const calledPosition = await api(`/api/queue/token/${called.id}/position`, {}, nextPatient.access_token);
assert(calledPosition.patient_guidance === "CALLED" && calledPosition.estimated_wait_minutes === 0 && calledPosition.recommended_return_at === null, "Called patient position still exposes a waiting estimate.");
const started = await api("/api/doctors/me/start-consultation", { method: "POST", body: JSON.stringify({ token_id: called.id }) }, doctor.access_token);
assert(started.status === "IN_CONSULTATION", "Doctor start-consultation did not transition the live token.");

const vital = await api("/api/vitals", {
  method: "POST",
  body: JSON.stringify({ token_id: called.id, temperature: 98.7, heart_rate: 76, blood_pressure: { systolic: 119, diastolic: 78 }, spo2: 99 }),
}, nurse.access_token);
assert(vital.token_id === called.id, "Nurse vitals were not stored against the current live token.");

const completed = await api("/api/doctors/me/complete-consultation", { method: "POST", body: JSON.stringify({ token_id: called.id }) }, doctor.access_token);
assert(completed.status === "COMPLETED", "Doctor completion did not persist the terminal token state.");

const socketToken = await api("/api/queue/token", {
  method: "POST",
  body: JSON.stringify({ department_id: ent.id, doctor_id: entDoctors[0].id }),
}, patientForSocket.access_token);
assert(socketToken.status === "WAITING", "Patient token creation did not persist a waiting MongoDB token.");

const socketUrl = base.replace(/^http/, "ws") + `/ws/patient/${socketToken.patient_id}`;
const socket = new WebSocket(socketUrl, ["opd-smartqueue", patientForSocket.access_token]);
await waitForEvent(socket, "CONNECTED");
const cancelledEvent = waitForEvent(socket, "TOKEN_CANCELLED");
const cancelled = await api(`/api/queue/token/${socketToken.id}/cancel`, { method: "POST" }, patientForSocket.access_token);
assert(cancelled.status === "CANCELLED", "Patient cancellation did not persist the terminal token state.");
await cancelledEvent;
socket.close();

const [overview, notifications, refreshedQueue] = await Promise.all([
  api("/api/analytics/overview", {}, admin.access_token),
  api("/api/patients/me/notifications", {}, currentPatient.access_token),
  api("/api/doctors/me/queue", {}, doctor.access_token),
]);
assert(overview.total_tokens >= 6, "Atlas-backed analytics did not include seeded queue records.");
assert(notifications.length > 0, "Patient notification records were not returned from MongoDB.");
assert(refreshedQueue.every((item) => ["WAITING", "CALLED", "IN_CONSULTATION"].includes(item.status)), "Doctor queue returned an invalid token lifecycle state.");

console.log(JSON.stringify({
  api_base: base,
  health: true,
  role_logins: [admin.user.role, doctor.user.role, nurse.user.role, currentPatient.user.role],
  authorization_enforced: true,
  queue_lifecycle: [inConsultation.status, called.status, started.status, completed.status],
  vitals_recorded: vital.id,
  secure_websocket_event: "TOKEN_CANCELLED",
  analytics_total_tokens: overview.total_tokens,
}, null, 2));
