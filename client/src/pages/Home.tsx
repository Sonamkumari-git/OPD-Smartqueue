/**
 * Clinical Flight Deck landing canvas: asymmetric care rail, live-state hierarchy,
 * warm porcelain surfaces, and Queue Teal as the only active signal color.
 */
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  Activity,
  ArrowRight,
  BellRing,
  CheckCircle2,
  ChevronRight,
  Clock3,
  HeartPulse,
  LockKeyhole,
  MonitorUp,
  Radio,
  ShieldCheck,
  Stethoscope,
  UsersRound,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

const roles = [
  {
    name: "Patient",
    label: "Personal queue view",
    copy: "A clear place in line, a live return window, and private updates without a waiting-room refresh.",
    icon: UsersRound,
    detail: "Live token position",
  },
  {
    name: "Doctor",
    label: "Consultation control",
    copy: "Call, start, complete, and safely advance a queue with the relevant visit context in view.",
    icon: Stethoscope,
    detail: "Guarded queue actions",
  },
  {
    name: "Nurse",
    label: "Vitals workflow",
    copy: "Capture validated workflow vitals for the current visit and make them available to the assigned clinician.",
    icon: HeartPulse,
    detail: "No diagnosis functionality",
  },
  {
    name: "Admin",
    label: "Operational intelligence",
    copy: "Review live capacity, queue movement, audit activity, and the performance of the estimate service.",
    icon: MonitorUp,
    detail: "Aggregate analytics",
  },
];

const queueSteps = ["Token issued", "Live queue state", "Approaching notice", "Consultation handoff"];

function BrandMark() {
  return (
    <div className="flex items-center gap-3">
      <img
        src="/queue-assets/queue-pulse-logo.webp"
        alt="OPD SmartQueue queue pulse logo"
        className="h-11 w-11 object-contain"
      />
      <div className="leading-none">
        <p className="text-[11px] font-extrabold uppercase tracking-[0.22em] text-teal-700">OPD</p>
        <p className="mt-1 text-base font-extrabold tracking-[-0.05em] text-[#15334A]">SmartQueue</p>
      </div>
    </div>
  );
}

export default function Home() {
  const [selectedRole, setSelectedRole] = useState(roles[0].name);
  const activeRole = roles.find((role) => role.name === selectedRole) ?? roles[0];

  return (
    <div className="min-h-screen overflow-x-hidden bg-[#F6F4EE] text-[#15334A]">
      <div className="border-b border-[#15334A]/10 bg-[#15334A] px-4 py-2 text-center text-[11px] font-semibold tracking-[0.02em] text-white sm:px-6">
        Demonstration system only — waiting-time information is an estimate, not clinical advice.
      </div>

      <header className="relative z-20 mx-auto flex max-w-[1440px] items-center justify-between px-5 py-5 sm:px-8 lg:px-12">
        <BrandMark />
        <div className="hidden items-center gap-7 lg:flex">
          <a href="#workflow" className="text-sm font-bold text-[#15334A]/65 transition-colors hover:text-[#0F8F83]">Workflow</a>
          <a href="#architecture" className="text-sm font-bold text-[#15334A]/65 transition-colors hover:text-[#0F8F83]">Architecture</a>
          <div className="flex items-center gap-2 border-l border-[#15334A]/15 pl-6 text-xs font-extrabold text-[#15334A]">
            <span className="relative flex h-2.5 w-2.5"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#0F8F83]/45" /><span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-[#0F8F83]" /></span>
            LIVE-READY DESIGN
          </div>
        </div>
        <Button className="rounded-full bg-[#15334A] px-5 font-bold text-white shadow-[0_10px_25px_rgba(21,51,74,0.16)] hover:bg-[#0F8F83]" onClick={() => { window.location.href = "/sign-in"; }}>Explore demo <ArrowRight className="ml-1 h-4 w-4" /></Button>
      </header>

      <main>
        <section className="relative mx-auto grid max-w-[1440px] overflow-hidden px-5 pb-18 pt-7 sm:px-8 lg:grid-cols-[1.02fr_0.98fr] lg:px-12 lg:pb-24 lg:pt-15">
          <div className="relative z-10 max-w-2xl py-7 lg:py-16">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-[#0F8F83]/20 bg-white/75 px-3.5 py-2 text-xs font-extrabold uppercase tracking-[0.14em] text-[#0F8F83] shadow-sm">
              <Radio className="h-3.5 w-3.5" /> Live queue coordination
            </div>
            <h1 className="max-w-xl text-balance font-[Fraunces] text-5xl font-semibold leading-[0.98] tracking-[-0.055em] text-[#15334A] sm:text-6xl lg:text-7xl">
              Your place in the queue, made clear.
            </h1>
            <p className="mt-7 max-w-lg text-pretty text-base leading-7 text-[#15334A]/70 sm:text-lg">
              OPD SmartQueue brings token visibility, queue movement, workflow vitals, and realistic wait estimates into one privacy-conscious care console.
            </p>
            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button className="h-12 rounded-full bg-[#0F8F83] px-6 font-extrabold text-white shadow-[0_12px_28px_rgba(15,143,131,0.24)] hover:bg-[#0C756C]" onClick={() => document.getElementById("workflow")?.scrollIntoView({ behavior: "smooth" })}>
                See the care flow <ChevronRight className="ml-1 h-4 w-4" />
              </Button>
              <Button variant="outline" className="h-12 rounded-full border-[#15334A]/15 bg-white/65 px-6 font-extrabold text-[#15334A] hover:border-[#0F8F83]/40 hover:bg-white" onClick={() => document.getElementById("architecture")?.scrollIntoView({ behavior: "smooth" })}>
                View system design
              </Button>
            </div>
            <div className="mt-11 flex flex-wrap gap-x-7 gap-y-3 border-t border-[#15334A]/12 pt-6 text-xs font-bold text-[#15334A]/65">
              <span className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-[#0F8F83]" /> Role-aware access</span>
              <span className="flex items-center gap-2"><Activity className="h-4 w-4 text-[#0F8F83]" /> Live queue signals</span>
              <span className="flex items-center gap-2"><LockKeyhole className="h-4 w-4 text-[#0F8F83]" /> Minimum necessary data</span>
            </div>
          </div>

          <div className="relative z-10 min-h-[430px] lg:min-h-[590px]">
            <div className="absolute right-[-7rem] top-[-4rem] h-[36rem] w-[36rem] rounded-full bg-[#DDEFEA] blur-3xl" />
            <img src="/queue-assets/clinical-hero.webp" alt="Abstract outpatient care environment" className="absolute inset-0 h-full w-full rounded-[2.25rem] object-cover object-right shadow-[0_28px_70px_rgba(21,51,74,0.18)]" />
            <div className="absolute inset-0 rounded-[2.25rem] bg-gradient-to-tr from-[#15334A]/70 via-[#15334A]/5 to-transparent" />
            <div className="absolute bottom-5 left-5 right-5 rounded-[1.6rem] border border-white/25 bg-white/88 p-5 shadow-xl backdrop-blur-xl sm:bottom-8 sm:left-8 sm:right-auto sm:w-[310px]">
              <div className="flex items-center justify-between">
                <p className="text-[10px] font-extrabold uppercase tracking-[0.15em] text-[#15334A]/55">Live queue pulse</p>
                <span className="flex items-center gap-1.5 text-[10px] font-extrabold text-[#0F8F83]"><span className="h-2 w-2 rounded-full bg-[#0F8F83]" /> Connected</span>
              </div>
              <div className="mt-4 flex items-end justify-between">
                <div><p className="text-4xl font-extrabold tracking-[-0.07em] text-[#15334A]">C-150</p><p className="mt-1 text-xs font-bold text-[#15334A]/55">Your active token</p></div>
                <div className="rounded-2xl bg-[#E0F3EF] px-3 py-2 text-right"><p className="text-xl font-extrabold text-[#0F8F83]">7</p><p className="text-[9px] font-extrabold uppercase tracking-[0.09em] text-[#0F8F83]">ahead</p></div>
              </div>
              <div className="mt-5 h-1.5 overflow-hidden rounded-full bg-[#15334A]/10"><div className="h-full w-[47%] rounded-full bg-[#0F8F83]" /></div>
              <p className="mt-3 text-xs font-bold text-[#15334A]/65">Queue moving. Return window is approaching.</p>
            </div>
          </div>
        </section>

        <section id="workflow" className="relative overflow-hidden bg-[#15334A] py-18 text-white lg:py-24">
          <img src="/queue-assets/queue-pulse-texture.webp" alt="" className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-20 mix-blend-screen" />
          <div className="relative mx-auto max-w-[1440px] px-5 sm:px-8 lg:px-12">
            <div className="grid gap-10 lg:grid-cols-[0.82fr_1.18fr] lg:items-end">
              <div><p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#76D6CB]">A role-specific care rail</p><h2 className="mt-4 max-w-sm font-[Fraunces] text-4xl font-semibold leading-tight tracking-[-0.04em] sm:text-5xl">One shared queue. Four clear responsibilities.</h2></div>
              <p className="max-w-xl text-base leading-7 text-white/68">The queue is the common operational source of truth. Each role sees an intentionally limited workspace: patients follow their own token, staff operate the queue, and administrators review aggregate performance.</p>
            </div>

            <div className="mt-12 grid gap-3 md:grid-cols-4">
              {queueSteps.map((step, index) => <div key={step} className="group rounded-[1.5rem] border border-white/12 bg-white/[0.055] p-5 transition-transform duration-200 hover:-translate-y-1 hover:bg-white/[0.1]"><p className="text-xs font-extrabold text-[#76D6CB]">0{index + 1}</p><p className="mt-9 text-sm font-extrabold tracking-[-0.02em]">{step}</p><div className="mt-4 h-px bg-white/15"><div className="h-px w-1/2 bg-[#76D6CB] transition-all duration-300 group-hover:w-full" /></div></div>)}
            </div>

            <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_0.92fr]">
              <div className="rounded-[2rem] border border-white/12 bg-white/[0.06] p-6 sm:p-8">
                <div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-[11px] font-extrabold uppercase tracking-[0.17em] text-white/45">Role workspace preview</p><h3 className="mt-2 text-2xl font-extrabold tracking-[-0.05em]">{activeRole.label}</h3></div><activeRole.icon className="h-9 w-9 text-[#76D6CB]" /></div>
                <p className="mt-5 max-w-xl text-sm leading-6 text-white/70">{activeRole.copy}</p>
                <div className="mt-7 flex flex-wrap gap-2">{roles.map((role) => <button key={role.name} type="button" onClick={() => setSelectedRole(role.name)} className={cn("rounded-full border px-3 py-2 text-xs font-extrabold transition-all", selectedRole === role.name ? "border-[#76D6CB] bg-[#76D6CB] text-[#15334A]" : "border-white/15 bg-white/5 text-white/70 hover:border-white/35 hover:bg-white/10")}>{role.name}</button>)}</div>
                <div className="mt-7 flex items-center gap-3 border-t border-white/10 pt-5 text-xs font-bold text-[#76D6CB]"><CheckCircle2 className="h-4 w-4" /> {activeRole.detail}</div>
              </div>
              <div className="relative min-h-[300px] overflow-hidden rounded-[2rem] bg-[#F6F4EE] p-6 text-[#15334A] sm:p-8">
                <img src="/queue-assets/patient-mobile-queue.webp" alt="Abstract patient queue interface on a mobile phone" className="absolute bottom-0 right-0 h-full w-[54%] object-cover object-left opacity-90" />
                <div className="relative max-w-[48%]"><p className="text-[10px] font-extrabold uppercase tracking-[0.14em] text-[#15334A]/45">Patient first</p><p className="mt-3 font-[Fraunces] text-3xl font-semibold leading-tight tracking-[-0.04em]">Queue visibility that lets people step away with confidence.</p><div className="mt-6 flex items-center gap-2 text-xs font-extrabold text-[#0F8F83]"><BellRing className="h-4 w-4" /> Approaching and called alerts</div></div>
              </div>
            </div>
          </div>
        </section>

        <section id="architecture" className="mx-auto grid max-w-[1440px] gap-9 px-5 py-18 sm:px-8 lg:grid-cols-[0.78fr_1.22fr] lg:px-12 lg:py-24">
          <div><p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#0F8F83]">Build architecture</p><h2 className="mt-4 font-[Fraunces] text-4xl font-semibold leading-tight tracking-[-0.045em] text-[#15334A]">Every signal has an authoritative source.</h2><p className="mt-5 max-w-sm text-sm leading-6 text-[#15334A]/65">REST delivers recoverable state. FastAPI WebSockets deliver timely change. MongoDB preserves the historical record that informs queue analytics and model training.</p><Button variant="outline" className="mt-8 rounded-full border-[#15334A]/15 bg-white px-5 font-extrabold text-[#15334A] hover:border-[#0F8F83]/35 hover:bg-white" onClick={() => toast.success("Architecture details are documented in docs/PHASE_1_ARCHITECTURE.md.")}>Read the build map <ArrowRight className="ml-1 h-4 w-4" /></Button></div>
          <div className="grid gap-3 sm:grid-cols-2">
            {[{ icon: Activity, title: "Queue engine", copy: "Atomic counters, priority-aware FIFO ordering, guarded transitions, and auditable workflow events." }, { icon: Radio, title: "Live transport", copy: "Authorized queue, patient, and clinician channels reconnect to REST-backed truth." }, { icon: Clock3, title: "Wait estimates", copy: "A configurable rules baseline stays available beneath a trained regression model." }, { icon: ShieldCheck, title: "Privacy controls", copy: "JWT authentication, role checks, minimum-necessary events, and audit records shape every route." }].map((item) => <article key={item.title} className="rounded-[1.65rem] border border-[#15334A]/10 bg-white p-6 shadow-[0_12px_30px_rgba(21,51,74,0.045)]"><div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#E0F3EF] text-[#0F8F83]"><item.icon className="h-5 w-5" /></div><h3 className="mt-8 text-lg font-extrabold tracking-[-0.04em] text-[#15334A]">{item.title}</h3><p className="mt-3 text-sm leading-6 text-[#15334A]/62">{item.copy}</p></article>)}
          </div>
        </section>
      </main>

      <footer className="border-t border-[#15334A]/10 px-5 py-9 sm:px-8 lg:px-12"><div className="mx-auto flex max-w-[1440px] flex-col justify-between gap-5 text-xs font-semibold text-[#15334A]/55 sm:flex-row sm:items-center"><BrandMark /><p className="max-w-xl leading-5">OPD SmartQueue is a demonstration system for OPD queue and workflow management. It is not a certified hospital information system and does not diagnose, triage, or recommend treatment.</p></div></footer>
    </div>
  );
}
