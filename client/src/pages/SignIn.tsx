/**
 * Clinical Flight Deck access page: operational confidence, high contrast fields,
 * and plainly labelled local demonstration shortcuts.
 */
import { Button } from "@/components/ui/button";
import { useSession } from "@/contexts/SessionContext";
import { Activity, ArrowLeft, ArrowRight, LockKeyhole, ShieldCheck, Stethoscope, UserRound, UsersRound } from "lucide-react";
import { FormEvent, useState } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";

const demoRoles = [
  { role: "patient" as const, label: "Patient", note: "Follow token C-150", icon: UserRound },
  { role: "doctor" as const, label: "Doctor", note: "Manage today’s queue", icon: Stethoscope },
  { role: "nurse" as const, label: "Nurse", note: "Record visit vitals", icon: Activity },
  { role: "admin" as const, label: "Admin", note: "Review operations", icon: UsersRound },
];

export default function SignIn() {
  const [, navigate] = useLocation();
  const { signIn, demoSession } = useSession();
  const [email, setEmail] = useState("patient09@opdsmartqueue.local");
  const [password, setPassword] = useState("DemoPass!123");
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setBusy(true);
    try { const user = await signIn(email, password); toast.success(`Signed in as ${user.name}.`); navigate("/dashboard"); }
    catch (error) { toast.error(error instanceof Error ? error.message : "Unable to sign in. Start the local API and MongoDB, or use a demo preview."); }
    finally { setBusy(false); }
  };

  return <div className="min-h-screen bg-[#F6F4EE] text-[#15334A]">
    <div className="grid min-h-screen lg:grid-cols-[0.9fr_1.1fr]">
      <aside className="relative hidden overflow-hidden bg-[#15334A] p-12 text-white lg:flex lg:flex-col">
        <img src="/manus-storage/opd-queue-pulse-texture_6d0de524.png" alt="" className="absolute inset-0 h-full w-full object-cover opacity-25 mix-blend-screen" />
        <div className="relative flex items-center gap-3"><img src="/manus-storage/opd-queue-pulse-logo_b3eb1b9c.png" alt="OPD SmartQueue logo" className="h-11 w-11" /><p className="text-lg font-extrabold tracking-[-0.05em]">OPD SmartQueue</p></div>
        <div className="relative my-auto max-w-md"><p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#76D6CB]">Care access</p><h1 className="mt-5 font-[Fraunces] text-5xl font-semibold leading-tight tracking-[-0.05em]">Enter the queue with the context you need.</h1><p className="mt-6 leading-7 text-white/65">Patient access protects personal queue information. Clinical roles receive only the operational tools appropriate to their workflow.</p></div>
        <div className="relative flex items-center gap-3 border-t border-white/15 pt-6 text-xs font-bold text-white/65"><ShieldCheck className="h-4 w-4 text-[#76D6CB]" /> Demonstration interface; not a clinical decision system.</div>
      </aside>
      <main className="flex items-center justify-center px-5 py-10 sm:px-8">
        <div className="w-full max-w-xl"><button onClick={() => navigate("/")} className="mb-10 flex items-center gap-2 text-xs font-extrabold text-[#15334A]/55 hover:text-[#0F8F83]"><ArrowLeft className="h-4 w-4" /> Back to overview</button>
          <div className="rounded-[2rem] border border-[#15334A]/10 bg-white p-6 shadow-[0_20px_55px_rgba(21,51,74,0.09)] sm:p-9"><div className="flex items-start justify-between gap-5"><div><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#0F8F83]">Secure sign in</p><h2 className="mt-3 font-[Fraunces] text-4xl font-semibold tracking-[-0.05em]">Continue to your workspace.</h2></div><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#E0F3EF] text-[#0F8F83]"><LockKeyhole className="h-5 w-5" /></div></div>
            <form onSubmit={submit} className="mt-8 space-y-4"><label className="block text-xs font-extrabold uppercase tracking-[0.11em] text-[#15334A]/55">Email<input value={email} onChange={(event) => setEmail(event.target.value)} type="email" className="mt-2 h-12 w-full rounded-xl border border-[#15334A]/13 bg-[#F8F8F6] px-4 text-sm font-semibold outline-none transition focus:border-[#0F8F83] focus:ring-4 focus:ring-[#0F8F83]/10" /></label><label className="block text-xs font-extrabold uppercase tracking-[0.11em] text-[#15334A]/55">Password<input value={password} onChange={(event) => setPassword(event.target.value)} type="password" className="mt-2 h-12 w-full rounded-xl border border-[#15334A]/13 bg-[#F8F8F6] px-4 text-sm font-semibold outline-none transition focus:border-[#0F8F83] focus:ring-4 focus:ring-[#0F8F83]/10" /></label><Button disabled={busy} className="mt-2 h-12 w-full rounded-xl bg-[#0F8F83] font-extrabold text-white hover:bg-[#0C756C]">{busy ? "Checking access…" : "Sign in to workspace"}<ArrowRight className="ml-1 h-4 w-4" /></Button></form><p className="mt-5 text-sm font-semibold text-[#15334A]/60">New patient? <button type="button" onClick={() => navigate("/register")} className="font-extrabold text-[#0F8F83] hover:underline">Create your secure account.</button></p>
            <div className="mt-9 border-t border-[#15334A]/10 pt-7"><p className="text-xs font-extrabold uppercase tracking-[0.14em] text-[#15334A]/50">Explore the interface locally</p><p className="mt-2 text-sm leading-6 text-[#15334A]/62">Use a role preview if your local API or MongoDB service is not running. These previews contain clearly labelled demonstration data.</p><div className="mt-5 grid gap-2 sm:grid-cols-2">{demoRoles.map(({ role, label, note, icon: Icon }) => <button key={role} type="button" onClick={() => { demoSession(role); navigate("/dashboard"); }} className="group flex items-center gap-3 rounded-xl border border-[#15334A]/10 p-3 text-left transition hover:border-[#0F8F83]/40 hover:bg-[#EAF6F3]"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#F0F3F2] text-[#0F8F83] group-hover:bg-white"><Icon className="h-4 w-4" /></div><span><span className="block text-sm font-extrabold">{label}</span><span className="block text-xs text-[#15334A]/55">{note}</span></span></button>)}</div></div>
          </div>
        </div>
      </main>
    </div>
  </div>;
}
