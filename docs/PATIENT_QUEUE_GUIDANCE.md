# Patient Queue Guidance

The prior patient dashboard displayed a `0–1 minutes` wait estimate and `Awaiting call` return guidance even after the token had transitioned to `IN_CONSULTATION`. That was misleading because the patient was no longer waiting.

The queue-position API now returns explicit patient guidance for `WAITING`, `CALLED`, and `IN_CONSULTATION` states. The patient workspace renders a wait estimate only for `WAITING`; it instead shows `Please proceed now` for `CALLED` and `Consultation in progress` for `IN_CONSULTATION`.

The coordinated Render deployment was detected through the public frontend bundle and API readiness probes. A browser smoke test was initiated for an Atlas-backed patient account; the browser session reset before credential entry, so the automated API regression coverage remains the authoritative verification for the state-specific contract.

The real deployed API was then queried for the live token `E-009`, which was in `IN_CONSULTATION`. It returned `patient_guidance: IN_CONSULTATION`, `estimated_wait_minutes: 0`, no recommended return time, and the notice `Your consultation is currently in progress.` This confirms the correction applies to the same type of active visit shown in the reported dashboards.
