/** Verify the secure FastAPI WebSocket path with live API-created patient data. */
const base = process.env.OPD_API_URL ?? "http://127.0.0.1:8000";
const password = "WsCheck2026A";

async function api(path, options = {}, accessToken) {
  const response = await fetch(`${base}${path}`, { ...options, headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}), ...(options.headers ?? {}) } });
  const body = await response.json();
  if (!response.ok || !body.success) throw new Error(body.message ?? `Request failed: ${path}`);
  return body.data;
}

function receive(ws, event) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Timed out waiting for ${event}`)), 7000);
    ws.addEventListener("message", ({ data }) => {
      const payload = JSON.parse(data);
      if (payload.event === event) { clearTimeout(timer); resolve(payload); }
    });
    ws.addEventListener("error", () => { clearTimeout(timer); reject(new Error("WebSocket connection failed")); }, { once: true });
  });
}

const email = `ws.${Date.now()}@example.com`;
const registration = await api("/api/auth/register", { method: "POST", body: JSON.stringify({ name: "WebSocket Check", email, password }) });
const departments = await api("/api/departments");
const department = departments.find((item) => item.code === "C") ?? departments[0];
const doctors = await api(`/api/doctors?department_id=${department.id}`);
const doctor = doctors[0];
const token = await api("/api/queue/token", { method: "POST", body: JSON.stringify({ department_id: department.id, doctor_id: doctor.id }) }, registration.access_token);
const wsUrl = base.replace(/^http/, "ws") + `/ws/patient/${token.patient_id}`;
const socket = new WebSocket(wsUrl, ["opd-smartqueue", registration.access_token]);
await receive(socket, "CONNECTED");
const cancelled = receive(socket, "TOKEN_CANCELLED");
await api(`/api/queue/token/${token.id}/cancel`, { method: "POST" }, registration.access_token);
const event = await cancelled;
socket.close();
console.log(JSON.stringify({ secure_subprotocol: true, received_event: event.event, token_number: event.token_number }));
