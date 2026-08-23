/** Clinical Flight Deck registration: real patient onboarding only, never a demo identity. */
import { Button } from "@/components/ui/button";
import { useSession } from "@/contexts/SessionContext";
import { ArrowLeft, ArrowRight, ShieldCheck, UserPlus } from "lucide-react";
import { FormEvent, useState } from "react";
import { useLocation } from "wouter";
import { toast } from "sonner";

export default function Register() {
  const [, navigate] = useLocation();
  const { register } = useSession();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "", confirm: "" });
  const [busy, setBusy] = useState(false);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (form.password !== form.confirm) return toast.error("Password confirmation does not match.");
    setBusy(true);
    try {
      const user = await register({ name: form.name, email: form.email, phone: form.phone || undefined, password: form.password });
      toast.success(`Welcome, ${user.name}. Your patient workspace is ready.`);
      navigate("/dashboard");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Unable to create your account.");
    } finally {
      setBusy(false);
    }
  };

  const input = (label: string, key: keyof typeof form, type = "text") => (
    <label className="block text-xs font-extrabold uppercase tracking-[0.11em] text-[#15334A]/55">
      {label}
      <input
        required={key !== "phone"}
        value={form[key]}
        type={type}
        onChange={(event) => setForm({ ...form, [key]: event.target.value })}
        className="mt-2 h-12 w-full rounded-xl border border-[#15334A]/13 bg-[#F8F8F6] px-4 text-sm font-semibold normal-case tracking-normal outline-none transition focus:border-[#0F8F83] focus:ring-4 focus:ring-[#0F8F83]/10"
      />
    </label>
  );

  return (
    <div className="min-h-screen bg-[#F6F4EE] px-5 py-10 text-[#15334A] sm:px-8">
      <main className="mx-auto grid max-w-5xl overflow-hidden rounded-[2rem] border border-[#15334A]/10 bg-white shadow-[0_20px_55px_rgba(21,51,74,0.09)] lg:grid-cols-[0.78fr_1.22fr]">
        <section className="hidden bg-[#15334A] p-10 text-white lg:block">
          <div className="flex items-center gap-3"><img src="/queue-assets/queue-pulse-logo.webp" alt="OPD SmartQueue logo" className="h-11 w-11" /><p className="font-extrabold tracking-[-0.05em]">OPD SmartQueue</p></div>
          <div className="mt-32"><p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#76D6CB]">Patient account</p><h1 className="mt-5 font-[Fraunces] text-5xl font-semibold leading-tight tracking-[-0.05em]">A clearer path into today’s queue.</h1><p className="mt-6 leading-7 text-white/65">Create your account, select an available OPD department and clinician, then keep your own queue details in view.</p></div>
          <p className="mt-28 flex gap-2 border-t border-white/15 pt-5 text-xs font-bold text-white/65"><ShieldCheck className="h-4 w-4 text-[#76D6CB]" /> Workflow support only. Not a clinical decision system.</p>
        </section>
        <section className="p-7 sm:p-10">
          <button onClick={() => navigate("/sign-in")} className="flex items-center gap-2 text-xs font-extrabold text-[#15334A]/55 hover:text-[#0F8F83]"><ArrowLeft className="h-4 w-4" /> Back to sign in</button>
          <div className="mt-10 flex items-start justify-between"><div><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-[#0F8F83]">Patient registration</p><h2 className="mt-3 font-[Fraunces] text-4xl font-semibold tracking-[-0.05em]">Set up secure access.</h2></div><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[#E0F3EF] text-[#0F8F83]"><UserPlus className="h-5 w-5" /></div></div>
          <form onSubmit={submit} className="mt-8 grid gap-4 sm:grid-cols-2">
            {input("Full name", "name")}{input("Email", "email", "email")}{input("Phone (optional)", "phone", "tel")}{input("Password", "password", "password")}
            <div className="sm:col-span-2">{input("Confirm password", "confirm", "password")}</div>
            <Button disabled={busy} className="sm:col-span-2 mt-2 h-12 rounded-xl bg-[#0F8F83] font-extrabold text-white hover:bg-[#0C756C]">{busy ? "Creating your account…" : "Create patient account"}<ArrowRight className="ml-1 h-4 w-4" /></Button>
          </form>
          <p className="mt-6 text-sm font-semibold text-[#15334A]/60">Already registered? <button className="text-[#0F8F83] hover:underline" onClick={() => navigate("/sign-in")}>Sign in to your workspace.</button></p>
        </section>
      </main>
    </div>
  );
}
