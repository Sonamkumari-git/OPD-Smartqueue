/**
 * Clinical Flight Deck data boundary: REST is authoritative, and no UI component
 * handles tokens or request envelopes directly.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Role = "patient" | "doctor" | "nurse" | "admin";

export type SessionUser = {
  id: string;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
};

export type Token = {
  id: string;
  token_number: string;
  patient_id: string;
  doctor_id: string;
  department_id: string;
  status: "WAITING" | "CALLED" | "IN_CONSULTATION" | "COMPLETED" | "SKIPPED" | "CANCELLED";
  priority: "NORMAL" | "HIGH" | "EMERGENCY";
  queue_date: string;
  created_at: string;
  called_at?: string | null;
};

export type QueuePosition = {
  token_id: string;
  token_number: string;
  position: number | null;
  patients_ahead: number;
  queue_length: number;
  currently_serving: string | null;
  doctor_status: string;
  baseline_wait_minutes: number;
  estimated_wait_minutes: number;
  estimate_lower_minutes: number;
  estimate_upper_minutes: number;
  model_version: string;
  prediction_source: "baseline" | "trained_model";
  recommended_return_at: string | null;
  estimate_notice: string;
};

type Envelope<T> = { success: boolean; data: T; message?: string; error_code?: string };

async function request<T>(path: string, options: RequestInit = {}, accessToken?: string | null): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(options.headers ?? {}),
    },
  });
  const body = (await response.json().catch(() => null)) as Envelope<T> | null;
  if (!response.ok || !body?.success) throw new Error(body?.message ?? "The service is currently unavailable.");
  return body.data;
}

export const api = {
  login: (email: string, password: string) => request<{ access_token: string; user: SessionUser; expires_in_minutes: number }>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (payload: { name: string; email: string; password: string; phone?: string }) => request<{ access_token: string; user: SessionUser }>("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  me: (token: string) => request<SessionUser>("/api/auth/me", {}, token),
  departments: () => request<Array<{ id: string; name: string; code: string; description?: string }>>("/api/departments"),
  doctors: (departmentId?: string) => request<Array<{ id: string; name: string; department_id: string; specialization: string; status: string }>>(`/api/doctors${departmentId ? `?department_id=${departmentId}` : ""}`),
  myTokens: (token: string) => request<Token[]>("/api/patients/me/tokens", {}, token),
  notifications: (token: string) => request<Array<{ id: string; type: string; message: string; is_read: boolean; created_at: string }>>("/api/patients/me/notifications", {}, token),
  queuePosition: (tokenId: string, token: string) => request<QueuePosition>(`/api/queue/token/${tokenId}/position`, {}, token),
  createToken: (payload: { department_id: string; doctor_id: string }, token: string) => request<Token>("/api/queue/token", { method: "POST", body: JSON.stringify(payload) }, token),
  doctorQueue: (token: string) => request<Token[]>("/api/doctors/me/queue", {}, token),
  callNext: (token: string) => request<Token>("/api/doctors/me/call-next", { method: "POST" }, token),
  startConsultation: (tokenId: string, token: string) => request<Token>("/api/doctors/me/start-consultation", { method: "POST", body: JSON.stringify({ token_id: tokenId }) }, token),
  completeConsultation: (tokenId: string, token: string) => request<Token>("/api/doctors/me/complete-consultation", { method: "POST", body: JSON.stringify({ token_id: tokenId }) }, token),
  skipPatient: (tokenId: string, token: string) => request<Token>("/api/doctors/me/skip-patient", { method: "POST", body: JSON.stringify({ token_id: tokenId }) }, token),
  recordVitals: (payload: { token_id: string; temperature: number; heart_rate: number; blood_pressure: { systolic: number; diastolic: number }; spo2: number }, token: string) => request("/api/vitals", { method: "POST", body: JSON.stringify(payload) }, token),
  nurseQueue: (token: string) => request<Array<{ id: string; token_number: string; patient_id: string; patient_name: string; status: string }>>("/api/nurse/queue", {}, token),
  overview: (token: string) => request<Record<string, number>>("/api/analytics/overview", {}, token),
  departmentAnalytics: (token: string) => request<Array<Record<string, string | number>>>("/api/analytics/departments", {}, token),
  doctorAnalytics: (token: string) => request<Array<Record<string, string | number>>>("/api/analytics/doctors", {}, token),
  hourlyAnalytics: (token: string) => request<Array<{ hour: number; patients: number }>>("/api/analytics/hourly", {}, token),
};
