/**
 * Clinical Flight Deck patient workspace: treatment states communicate care progress,
 * while queue estimates remain visible only when the patient is genuinely waiting.
 */
import { Button } from "@/components/ui/button";
import { useSession } from "@/contexts/SessionContext";
import { useQueueSocket } from "@/hooks/useQueueSocket";
import { api, type Department, type Doctor, type Notification, type QueuePosition, type Token } from "@/services/api";
import { BellRing, ChevronRight, Clock3, LayoutDashboard, LogOut, Radio, UserRound, XCircle } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { useLocation } from "wouter";

type PatientState = { tokens: Token[]; active: Token | null; position: QueuePosition | null; notifications: Notification[]; departments: Department[]; doctors: Doctor[] };
const emptyState: PatientState = { tokens: [], active: null, position: null, notifications: [], departments: [], doctors: [] };
const stamp = (value?: string | null) => value ? new Date(value).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) : "—";

function Panel({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <section className={`rounded-[1.65rem] border border-[#15334A]/10 bg-white p-5 shadow-[0_10px_28px_rgba(21,51,74,0.035)] ${className}`}>{children}</section>;
}

export default function PatientDashboard() {
  const { user, accessToken, ready, signOut } = useSession();
  const [, navigate] = useLocation();
  const [state, setState] = useState<PatientState>(emptyState);
  const [loading, setLoading] = useState(true);
  const [departmentId, setDepartmentId] = useState("");
  const [doctorId, setDoctorId] = useState("");
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    if (!accessToken || !user || user.role !== "patient") return;
    try {
      const [tokens, notifications, departments] = await Promise.all([api.myTokens(accessToken), api.notifications(accessToken), api.departments()]);
      const active = tokens.find((item) => ["WAITING", "CALLED", "IN_CONSULTATION"].includes(item.status)) ?? null;
      const position = active ? await api.queuePosition(active.id, accessToken) : null;
      setState({ tokens, active, position, notifications, departments, doctors: [] });
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to refresh your live queue information.");
    } finally {
      setLoading(false);
    }
  }, [accessToken, user]);

  useEffect(() => { void refresh(); }, [refresh]);
  useEffect(() => {
    if (!departmentId) return;
    api.doctors(departmentId).then((doctors) => setState((current) => ({ ...current, doctors }))).catch((error) => toast.error(error.message));
  }, [departmentId]);

  const socketPath = useMemo(() => accessToken && state.active ? `/ws/patient/${state.active.patient_id}` : null, [accessToken, state.active]);
  const connection = useQueueSocket(socketPath, accessToken, refresh);
  const active = state.active;
  const position = state.position;
  const guidance = position?.patient_guidance ?? active?.status;
  const inConsultation = guidance === "IN_CONSULTATION";
  const called = guidance === "CALLED";

  const generate = async () => {
    if (!accessToken || !departmentId || !doctorId) return toast.error("Choose an available department and clinician first.");
    setBusy(true);
    try {
      await api.createToken({ department_id: departmentId, doctor_id: doctorId }, accessToken);
      toast.success("Your OPD token was generated.");
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to generate token.");
    } finally {
      setBusy(false);
    }
  };

  const cancel = async () => {
    if (!accessToken || !active || !window.confirm("Cancel your waiting token? This cannot be undone.")) return;
    try {
      await api.cancelToken(active.id, accessToken);
      toast.success("Token cancelled.");
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to cancel token.");
    }
  };

  const markAll = async () => {
    if (!accessToken) return;
    try {
      await api.markAllNotificationsRead(accessToken);
      await refresh();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to update notifications.");
    }
  };

  if (!ready || !user || user.role !== "patient") return <div className="min-h-screen bg-[#F6F4EE]" />;
  return <div className="min-h-screen bg-[#F6F4EE] text-[#15334A] lg:grid lg:grid-cols-[248px_1fr]"><aside className="flex items-center justify-between border-b border-[#15334A]/10 bg-white px-5 py-4 lg:min-h-screen lg:flex-col lg:items-stretch lg:border-b-0 lg:border-r lg:px-6 lg:py-7"><div className="flex items-center gap-2.5"><img src="/queue-assets/queue-pulse-logo.webp" alt="OPD SmartQueue logo" className="h-9 w-9" /><span className="text-[15px] font-extrabold tracking-[-0.055em]">OPD SmartQueue</span></div><nav className="hidden gap-2 lg:my-auto lg:flex lg:flex-col"><span className="flex items-center gap-3 rounded-xl bg-[#E0F3EF] px-3 py-3 text-sm font-extrabold text-[#0F8F83]"><LayoutDashboard className="h-4 w-4" /> Workspace</span><span className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-bold text-[#15334A]/55"><Radio className="h-4 w-4" /> Live updates</span><span className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-bold text-[#15334A]/55"><BellRing className="h-4 w-4" /> Recorded events</span></nav><button onClick={() => { signOut(); navigate("/"); }} className="flex items-center gap-2 text-xs font-extrabold text-[#15334A]/55 hover:text-[#0F8F83]"><LogOut className="h-4 w-4" /><span className="hidden lg:inline">Sign out</span></button></aside><main className="min-w-0"><header className="flex flex-wrap items-center justify-between gap-4 border-b border-[#15334A]/10 px-5 py-5 sm:px-8 lg:px-10"><div><div className="flex items-center gap-2 text-xs font-extrabold uppercase tracking-[0.14em] text-[#0F8F83]"><UserRound className="h-3.5 w-3.5" /> Patient workspace</div><h1 className="mt-1 text-2xl font-extrabold tracking-[-0.05em]">Your queue and visit history</h1></div><span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10px] font-extrabold uppercase tracking-[0.08em] ${connection === "connected" ? "bg-[#DDF3EE] text-[#0F8F83]" : "bg-[#FFF2D8] text-[#9D6A10]"}`}><span className={`h-1.5 w-1.5 rounded-full ${connection === "connected" ? "bg-[#0F8F83]" : "bg-[#D7951D]"}`} />{connection === "connected" ? "Live" : connection}</span></header><div className="space-y-5 px-5 py-7 sm:px-8 lg:px-10 lg:py-9">{loading ? <div className="grid gap-4 sm:grid-cols-3"><div className="h-40 animate-pulse rounded-[1.5rem] bg-white" /><div className="h-40 animate-pulse rounded-[1.5rem] bg-white" /><div className="h-40 animate-pulse rounded-[1.5rem] bg-white" /></div> : active && position ? <><div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]"><section className="overflow-hidden rounded-[2rem] bg-[#15334A] p-6 text-white sm:p-8"><div className="flex items-center justify-between"><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#76D6CB]">Your active token</p><span className="rounded-full bg-white/10 px-3 py-1 text-[10px] font-extrabold uppercase tracking-[0.1em]">{active.status.replace(/_/g, " ")}</span></div><div className="mt-7 flex flex-wrap items-end justify-between gap-5"><div><p className="font-[Fraunces] text-6xl font-semibold tracking-[-0.07em]">{active.token_number}</p><p className="mt-2 text-sm font-bold text-white/55">{active.department_name ?? "Selected OPD"} · {active.doctor_name ?? "Assigned clinician"}</p><p className="mt-2 text-sm font-bold text-white/70">{inConsultation ? "Your consultation is in progress." : called ? "You have been called. Please proceed to the consultation area." : <>Currently serving <span className="text-white">{position.currently_serving ?? "—"}</span></>}</p></div><div className="rounded-2xl bg-white/10 p-4"><p className="text-3xl font-extrabold tracking-[-0.06em]">{inConsultation ? "Now" : called ? "Your turn" : position.patients_ahead}</p><p className="mt-1 text-[10px] font-extrabold uppercase tracking-[0.1em] text-[#76D6CB]">{inConsultation ? "with clinician" : called ? "please proceed" : "patients ahead"}</p></div></div><div className="mt-10 h-2 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-[#76D6CB]" style={{ width: `${inConsultation || called ? 100 : Math.max(9, (1 - position.patients_ahead / Math.max(1, position.queue_length)) * 100)}%` }} /></div><p className="mt-3 text-xs font-bold text-white/60">{inConsultation ? "Care visit is active · live queue updates remain connected" : called ? "Your turn is active · please check in with the clinician" : `Live queue pulse · position ${position.position ?? "—"} of ${position.queue_length}`}</p>{active.status === "WAITING" && <Button onClick={cancel} variant="outline" className="mt-6 border-white/20 bg-white/5 font-extrabold text-white hover:bg-white/10 hover:text-white"><XCircle className="mr-1 h-4 w-4" /> Cancel waiting token</Button>}</section><Panel className={inConsultation ? "border-[#0F8F83]/20 bg-[#EAF6F3]" : ""}><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#0F8F83]">{inConsultation ? "Consultation status" : called ? "Your turn" : "Wait-time outlook"}</p>{inConsultation ? <><p className="mt-5 text-4xl font-extrabold tracking-[-0.06em]">Consultation in progress</p><p className="mt-3 text-sm font-bold text-[#15334A]/65">You are currently with {active.doctor_name ?? "your clinician"}. No queue waiting estimate applies during treatment.</p><div className="mt-7 rounded-2xl bg-white/70 p-4"><p className="text-xs font-extrabold uppercase tracking-[0.12em] text-[#0F8F83]">Live care state</p><p className="mt-1 text-xl font-extrabold">With your clinician</p><p className="mt-2 text-xs leading-5 text-[#15334A]/60">The dashboard will update when the consultation is completed.</p></div></> : called ? <><p className="mt-5 text-4xl font-extrabold tracking-[-0.06em]">Please proceed now</p><p className="mt-3 text-sm font-bold text-[#15334A]/65">Your token has been called. A waiting estimate no longer applies.</p><div className="mt-7 rounded-2xl bg-[#EAF6F3] p-4"><p className="text-xs font-extrabold uppercase tracking-[0.12em] text-[#0F8F83]">Current instruction</p><p className="mt-1 text-xl font-extrabold">Proceed to the consultation area</p><p className="mt-2 text-xs leading-5 text-[#15334A]/60">Your clinician will start the consultation when ready.</p></div></> : <><div className="mt-5 flex items-baseline gap-2"><span className="text-5xl font-extrabold tracking-[-0.07em]">{position.estimate_lower_minutes}–{position.estimate_upper_minutes}</span><span className="text-sm font-bold text-[#15334A]/55">minutes</span></div><p className="mt-2 text-sm font-bold text-[#15334A]/55">Baseline {position.baseline_wait_minutes} min · {position.model_version.replace(/_/g, " ")}</p><div className="mt-7 rounded-2xl bg-[#EAF6F3] p-4"><p className="text-xs font-extrabold uppercase tracking-[0.12em] text-[#0F8F83]">Recommended return</p><p className="mt-1 text-xl font-extrabold">{position.recommended_return_at ? new Date(position.recommended_return_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Awaiting call"}</p><p className="mt-2 text-xs leading-5 text-[#15334A]/60">{position.estimate_notice}</p></div></>}</Panel></div></> : <Panel><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#0F8F83]">New OPD visit</p><h2 className="mt-2 text-2xl font-extrabold tracking-[-0.05em]">Choose a department, clinician, and generate your token.</h2><div className="mt-6 grid gap-4 md:grid-cols-2"><label className="text-xs font-extrabold uppercase tracking-[0.1em] text-[#15334A]/55">Department<select value={departmentId} onChange={(event) => { setDepartmentId(event.target.value); setDoctorId(""); }} className="mt-2 h-11 w-full rounded-xl border border-[#15334A]/12 bg-[#F8F8F6] px-3 text-sm font-bold normal-case"><option value="">Choose department</option>{state.departments.map((department) => <option key={department.id} value={department.id}>{department.name}</option>)}</select></label><label className="text-xs font-extrabold uppercase tracking-[0.1em] text-[#15334A]/55">Available clinician<select disabled={!departmentId} value={doctorId} onChange={(event) => setDoctorId(event.target.value)} className="mt-2 h-11 w-full rounded-xl border border-[#15334A]/12 bg-[#F8F8F6] px-3 text-sm font-bold normal-case disabled:opacity-50"><option value="">Choose clinician</option>{state.doctors.map((doctor) => <option key={doctor.id} value={doctor.id}>{doctor.name} · {doctor.specialization} · {doctor.status}</option>)}</select></label></div><Button disabled={busy} onClick={generate} className="mt-6 rounded-xl bg-[#0F8F83] font-extrabold text-white hover:bg-[#0C756C]">{busy ? "Generating token…" : "Generate OPD token"}<ChevronRight className="ml-1 h-4 w-4" /></Button></Panel>}<div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]"><Panel><div className="flex items-center justify-between"><div><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#0F8F83]">Token history</p><h2 className="mt-1 text-xl font-extrabold tracking-[-0.04em]">Your recorded visit timeline</h2></div><Clock3 className="h-5 w-5 text-[#0F8F83]" /></div><div className="mt-5 divide-y divide-[#15334A]/8">{state.tokens.length ? state.tokens.map((item) => <div key={item.id} className="py-4"><div className="flex items-start justify-between gap-3"><div><p className="font-extrabold">{item.token_number} · {item.status.replace(/_/g, " ")}</p><p className="mt-1 text-sm font-semibold text-[#15334A]/55">{item.department_name ?? item.department_id} · {item.doctor_name ?? item.doctor_id}</p></div><p className="text-xs font-bold text-[#15334A]/45">{stamp(item.created_at)}</p></div><p className="mt-2 text-xs text-[#15334A]/55">Called {stamp(item.called_at)} · Started {stamp(item.consultation_started_at)} · Completed {stamp(item.completed_at)}</p></div>) : <p className="py-6 text-sm font-semibold text-[#15334A]/55">No token history yet.</p>}</div></Panel><Panel><div className="flex items-center justify-between"><div><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#0F8F83]">Personal notifications</p><h2 className="mt-1 text-xl font-extrabold tracking-[-0.04em]">Queue movement signals</h2></div><button onClick={markAll} className="text-xs font-extrabold text-[#0F8F83] hover:underline">Mark all read</button></div><div className="mt-5 space-y-3">{state.notifications.length ? state.notifications.map((note) => <button key={note.id} onClick={async () => { if (!note.is_read && accessToken) { await api.markNotificationRead(note.id, accessToken); await refresh(); } }} className={`w-full rounded-xl p-4 text-left ${note.is_read ? "bg-[#F7F8F7]" : "bg-[#EAF6F3]"}`}><p className="text-xs font-extrabold text-[#0F8F83]">{note.type.replace(/_/g, " ")}</p><p className="mt-2 text-sm font-bold leading-6">{note.message}</p><p className="mt-2 text-xs text-[#15334A]/45">{stamp(note.created_at)} · {note.is_read ? "read" : "mark read"}</p></button>) : <p className="text-sm font-semibold text-[#15334A]/55">No notifications yet.</p>}</div></Panel></div></div></main></div>;
}
