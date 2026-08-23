/**
 * Clinical Flight Deck access page: each role enters through a real sign-in route.
 * No shortcut creates a mock session; the FastAPI backend remains the sole identity source.
 */
import { Button } from "@/components/ui/button";
import { type Role } from "@/services/api";
import { Activity, ArrowLeft, ArrowRight, LockKeyhole, ShieldCheck, Stethoscope, UserRound, UsersRound } from "lucide-react";
import { FormEvent, useState } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";
import { useSession } from "@/contexts/SessionContext";

type SignInProps = { requiredRole?: Role };

const roleOptions: Array<{ role: Role; label: string; note: string; icon: typeof UserRound }> = [
  { role: "patient", label: "Patient", note: "Track your own tokens and visit history", icon: UserRound },
  { role: "doctor", label: "Doctor", note: "Manage your clinical queue", icon: Stethoscope },
  { role: "nurse", label: "Nurse", note: "Record authorized workflow vitals", icon: Activity },
  { role: "admin", label: "Admin", note: "Review operational analytics", icon: UsersRound },
];

const roleName = (role: Role) => role.charAt(0).toUpperCase() + role.slice(1);

export default function SignIn({ requiredRole }: SignInProps) {
  const [, navigate] = useLocation();
  const { signIn, signOut } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const selected = requiredRole ? roleOptions.find((item) => item.role === requiredRole) : null;
  const SelectedIcon = selected?.icon ?? LockKeyhole;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!requiredRole) return;
    setBusy(true);
    try {
      const user = await signIn(email, password);
      if (user.role !== requiredRole) {
        signOut();
        throw new Error(`This account belongs to the ${roleName(user.role)} workspace. Please choose the matching sign-in page.`);
      }
      toast.success(`Signed in to the ${roleName(user.role)} workspace.`);
      navigate(`/dashboard/${user.role}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to sign in to this workspace.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F6F4EE] text-[#15334A]">
      <div className="grid min-h-screen lg:grid-cols-[0.9fr_1.1fr]">
        <aside className="relative hidden overflow-hidden bg-[#15334A] p-12 text-white lg:flex lg:flex-col">
          <img src="/queue-assets/queue-pulse-texture.webp" alt="" className="absolute inset-0 h-full w-full object-cover opacity-25 mix-blend-screen" />
          <div className="relative flex items-center gap-3"><img src="/queue-assets/queue-pulse-logo.webp" alt="OPD SmartQueue logo" className="h-11 w-11" /><p className="text-lg font-extrabold tracking-[-0.05em]">OPD SmartQueue</p></div>
          <div className="relative my-auto max-w-md"><p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#76D6CB]">{selected ? `${selected.label} access` : "Choose your workspace"}</p><h1 className="mt-5 font-[Fraunces] text-5xl font-semibold leading-tight tracking-[-0.05em]">{selected ? `Sign in to the ${selected.label.toLowerCase()} workspace.` : "One secure door for every care role."}</h1><p className="mt-6 leading-7 text-white/65">Each workspace is authenticated against the live backend and displays only the operational data permitted for that role.</p></div>
          <div className="relative flex items-center gap-3 border-t border-white/15 pt-6 text-xs font-bold text-white/65"><ShieldCheck className="h-4 w-4 text-[#76D6CB]" /> No preview sessions or synthetic access on the deployed service.</div>
        </aside>

        <main className="flex items-center justify-center px-5 py-10 sm:px-8">
          <div className="w-full max-w-xl">
            <button onClick={() => navigate(selected ? "/sign-in" : "/")} className="mb-10 flex items-center gap-2 text-xs font-extrabold text-[#15334A]/55 hover:text-[#0F8F83]"><ArrowLeft className="h-4 w-4" /> {selected ? "Choose another workspace" : "Back to overview"}</button>

            {selected ? (
              <div className="rounded-[2rem] border border-[#15334A]/10 bg-white p-6 shadow-[0_20px_55px_rgba(21,51,74,0.09)] sm:p-9">
                <div className="flex items-start justify-between gap-5"><div><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#0F8F83]">{selected.label} sign in</p><h2 className="mt-3 font-[Fraunces] text-4xl font-semibold tracking-[-0.05em]">Open your role workspace.</h2></div><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#E0F3EF] text-[#0F8F83]"><SelectedIcon className="h-5 w-5" /></div></div>
                <p className="mt-4 text-sm leading-6 text-[#15334A]/62">{selected.note}. Enter the credentials provisioned for your {selected.label.toLowerCase()} account.</p>
                <form onSubmit={submit} className="mt-8 space-y-4"><label className="block text-xs font-extrabold uppercase tracking-[0.11em] text-[#15334A]/55">Email<input required value={email} onChange={(event) => setEmail(event.target.value)} type="email" autoComplete="email" className="mt-2 h-12 w-full rounded-xl border border-[#15334A]/13 bg-[#F8F8F6] px-4 text-sm font-semibold outline-none transition focus:border-[#0F8F83] focus:ring-4 focus:ring-[#0F8F83]/10" /></label><label className="block text-xs font-extrabold uppercase tracking-[0.11em] text-[#15334A]/55">Password<input required value={password} onChange={(event) => setPassword(event.target.value)} type="password" autoComplete="current-password" className="mt-2 h-12 w-full rounded-xl border border-[#15334A]/13 bg-[#F8F8F6] px-4 text-sm font-semibold outline-none transition focus:border-[#0F8F83] focus:ring-4 focus:ring-[#0F8F83]/10" /></label><Button disabled={busy} className="mt-2 h-12 w-full rounded-xl bg-[#0F8F83] font-extrabold text-white hover:bg-[#0C756C]">{busy ? "Checking access…" : `Sign in as ${selected.label}`}<ArrowRight className="ml-1 h-4 w-4" /></Button></form>
                {requiredRole === "patient" ? <p className="mt-5 text-sm font-semibold text-[#15334A]/60">New patient? <button type="button" onClick={() => navigate("/register")} className="font-extrabold text-[#0F8F83] hover:underline">Create your secure account.</button></p> : <p className="mt-5 text-sm leading-6 text-[#15334A]/60">Staff accounts are provisioned by an administrator. Ask your organization’s OPD administrator if you need access.</p>}
              </div>
            ) : (
              <div className="rounded-[2rem] border border-[#15334A]/10 bg-white p-6 shadow-[0_20px_55px_rgba(21,51,74,0.09)] sm:p-9">
                <div className="flex items-start justify-between gap-5"><div><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#0F8F83]">Secure role access</p><h2 className="mt-3 font-[Fraunces] text-4xl font-semibold tracking-[-0.05em]">Which workspace do you need?</h2></div><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#E0F3EF] text-[#0F8F83]"><LockKeyhole className="h-5 w-5" /></div></div>
                <p className="mt-4 text-sm leading-6 text-[#15334A]/62">Choose your role to open its dedicated sign-in page. After the backend verifies your credentials, you are taken to the corresponding live dashboard.</p>
                <div className="mt-8 grid gap-3 sm:grid-cols-2">{roleOptions.map(({ role, label, note, icon: Icon }) => <button key={role} type="button" onClick={() => navigate(`/sign-in/${role}`)} className="group flex min-h-32 items-start gap-4 rounded-2xl border border-[#15334A]/10 p-4 text-left transition hover:-translate-y-0.5 hover:border-[#0F8F83]/45 hover:bg-[#EAF6F3]"><div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#F0F3F2] text-[#0F8F83] group-hover:bg-white"><Icon className="h-5 w-5" /></div><span><span className="block text-sm font-extrabold">{label}</span><span className="mt-1 block text-xs leading-5 text-[#15334A]/55">{note}</span><span className="mt-3 inline-flex items-center text-xs font-extrabold text-[#0F8F83]">Open {label} sign in <ArrowRight className="ml-1 h-3.5 w-3.5" /></span></span></button>)}</div>
                <p className="mt-6 text-sm leading-6 text-[#15334A]/60">Patients can self-register. Doctor, nurse, and administrator accounts must be provisioned by an authorized administrator.</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
