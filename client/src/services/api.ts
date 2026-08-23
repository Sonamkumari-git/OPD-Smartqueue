/**
 * Clinical Flight Deck data boundary: REST is authoritative for every authenticated workflow.
 * Demo views never call these methods with fabricated responses.
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type Role = "patient" | "doctor" | "nurse" | "admin";
export type TokenStatus = "WAITING" | "CALLED" | "IN_CONSULTATION" | "COMPLETED" | "SKIPPED" | "CANCELLED";
export type SessionUser = { id: string; name: string; email: string; role: Role; is_active: boolean };
export type Department = { id: string; name: string; code: string; description?: string };
export type Doctor = { id: string; name: string; department_id: string; specialization: string; status: string };
export type Token = { id: string; token_number: string; patient_id: string; doctor_id: string; department_id: string; status: TokenStatus; priority: "NORMAL" | "HIGH" | "EMERGENCY"; queue_date: string; created_at: string; called_at?: string | null; consultation_started_at?: string | null; completed_at?: string | null; cancelled_at?: string | null; department_name?: string; doctor_name?: string; patient_name?: string };
export type QueuePosition = { token_id: string; token_number: string; position: number | null; patients_ahead: number; consultation_in_progress_ahead?: boolean; queue_length: number; currently_serving: string | null; doctor_status: string; baseline_wait_minutes: number; estimated_wait_minutes: number; estimate_lower_minutes: number; estimate_upper_minutes: number; model_version: string; prediction_source: "baseline" | "trained_model"; recommended_return_at: string | null; estimate_notice: string; patient_guidance: "WAITING" | "CALLED" | "IN_CONSULTATION" };
export type Notification = { id: string; type: string; message: string; is_read: boolean; created_at: string };
export type Vitals = { id: string; patient_id: string; token_id: string; recorded_by: string; temperature: number; heart_rate: number; blood_pressure: { systolic: number; diastolic: number }; spo2: number; recorded_at: string };
export type NurseVisit = { id: string; token_number: string; patient_id: string; doctor_id: string; department_id: string; patient_name: string; status: TokenStatus; created_at: string };
export type AnalyticsOverview = { total_tokens: number; total_patients: number; patients_waiting: number; patients_in_service: number; consultations_completed: number; skipped_tokens: number; cancelled_tokens: number; active_doctors: number; average_wait_minutes: number; maximum_wait_minutes: number; average_consultation_minutes: number };
export type Trends = { hourly_arrivals: Array<{ hour: number; patients: number }>; waiting_time_trend: Array<{ hour: number; average_wait_minutes: number }>; consultation_duration_trend: Array<{ hour: number; average_consultation_minutes: number }> };
type ValidationDetail = { loc?: Array<string | number>; msg?: string };
type Envelope<T> = { success: boolean; data: T; message?: string; error_code?: string; details?: ValidationDetail[] };

function messageForError(body: Envelope<unknown> | null) {
  const detail = body?.details?.[0];
  if (detail?.msg) {
    const field = detail.loc?.at(-1);
    const label = typeof field === "string" ? field.replace(/_/g, " ") : "Input";
    return `${label.charAt(0).toUpperCase()}${label.slice(1)}: ${detail.msg}.`;
  }
  return body?.message ?? "The service is currently unavailable.";
}

async function request<T>(path: string, options: RequestInit = {}, accessToken?: string | null): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers: { "Content-Type": "application/json", ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}), ...(options.headers ?? {}) } });
  const body = (await response.json().catch(() => null)) as Envelope<T> | null;
  if (!response.ok || !body?.success) throw new Error(messageForError(body));
  return body.data;
}
const query = (values: Record<string, string | undefined>) => {
  const params = new URLSearchParams(Object.entries(values).filter(([, value]) => Boolean(value)) as Array<[string, string]>);
  return params.size ? `?${params}` : "";
};

export const api = {
  login: (email: string, password: string) => request<{ access_token: string; user: SessionUser; expires_in_minutes: number }>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  register: (payload: { name: string; email: string; password: string; phone?: string }) => request<{ access_token: string; user: SessionUser }>("/api/auth/register", { method: "POST", body: JSON.stringify(payload) }),
  me: (token: string) => request<SessionUser>("/api/auth/me", {}, token),
  departments: () => request<Department[]>("/api/departments"),
  doctors: (departmentId?: string) => request<Doctor[]>(`/api/doctors${query({ department_id: departmentId })}`),
  myTokens: (token: string) => request<Token[]>("/api/patients/me/tokens", {}, token),
  notifications: (token: string) => request<Notification[]>("/api/patients/me/notifications", {}, token),
  markNotificationRead: (id: string, token: string) => request<Notification>(`/api/notifications/${id}/read`, { method: "PATCH" }, token),
  markAllNotificationsRead: (token: string) => request<{ updated: number }>("/api/notifications/read-all", { method: "PATCH" }, token),
  queuePosition: (tokenId: string, token: string) => request<QueuePosition>(`/api/queue/token/${tokenId}/position`, {}, token),
  createToken: (payload: { department_id: string; doctor_id: string }, token: string) => request<Token>("/api/queue/token", { method: "POST", body: JSON.stringify(payload) }, token),
  cancelToken: (tokenId: string, token: string) => request<Token>(`/api/queue/token/${tokenId}/cancel`, { method: "POST" }, token),
  setPriority: (tokenId: string, priority: Token["priority"], token: string) => request<Token>(`/api/queue/token/${tokenId}/priority`, { method: "PATCH", body: JSON.stringify({ priority }) }, token),
  doctorQueue: (token: string) => request<Token[]>("/api/doctors/me/queue", {}, token),
  callNext: (token: string) => request<Token>("/api/doctors/me/call-next", { method: "POST" }, token),
  startConsultation: (tokenId: string, token: string) => request<Token>("/api/doctors/me/start-consultation", { method: "POST", body: JSON.stringify({ token_id: tokenId }) }, token),
  completeConsultation: (tokenId: string, token: string) => request<Token>("/api/doctors/me/complete-consultation", { method: "POST", body: JSON.stringify({ token_id: tokenId }) }, token),
  skipPatient: (tokenId: string, token: string) => request<Token>("/api/doctors/me/skip-patient", { method: "POST", body: JSON.stringify({ token_id: tokenId }) }, token),
  updateDoctorStatus: (status: "AVAILABLE" | "BUSY" | "ON_BREAK" | "OFFLINE", token: string) => request<Doctor>("/api/doctors/me/status", { method: "PATCH", body: JSON.stringify({ status }) }, token),
  nurseQueue: (token: string) => request<NurseVisit[]>("/api/nurse/queue", {}, token),
  recordVitals: (payload: { token_id: string; temperature: number; heart_rate: number; blood_pressure: { systolic: number; diastolic: number }; spo2: number }, token: string) => request<Vitals>("/api/vitals", { method: "POST", body: JSON.stringify(payload) }, token),
  patientVitals: (patientId: string, token: string) => request<Vitals[]>(`/api/vitals/${patientId}`, {}, token),
  overview: (token: string, filters: Record<string, string | undefined> = {}) => request<AnalyticsOverview>(`/api/analytics/overview${query(filters)}`, {}, token),
  departmentAnalytics: (token: string, filters: Record<string, string | undefined> = {}) => request<Array<Record<string, string | number>>>(`/api/analytics/departments${query(filters)}`, {}, token),
  doctorAnalytics: (token: string, filters: Record<string, string | undefined> = {}) => request<Array<Record<string, string | number>>>(`/api/analytics/doctors${query(filters)}`, {}, token),
  trends: (token: string, filters: Record<string, string | undefined> = {}) => request<Trends>(`/api/analytics/trends${query(filters)}`, {}, token),
};
