# Atlas Seed and Workflow Validation Record

The schema-compatible seed workflow was exercised twice against the local MongoDB instance and remained idempotent. It persisted the expected test dataset: three departments, eighteen seeded users, six active queue tokens, and eighteen historical consultations.

The end-to-end verifier then authenticated four roles through FastAPI, enforced patient-to-admin authorization boundaries, completed a real queue lifecycle, recorded nurse vitals, queried analytics, and received a secure `TOKEN_CANCELLED` WebSocket event.

During that exercise, persisted MongoDB timestamps were found to deserialize as naive datetimes while application timestamps were timezone-aware. The MongoDB client is now configured for timezone-aware reads, with an integration regression test covering consultation completion. The corrected backend revision is being deployed to the Render API before the same controlled seed and verification steps are run against the configured Atlas database.

The Render API deployment for commit `0fef181` was confirmed as started through the service dashboard. Live database writes will not begin until that revision is reported as live.

The controlled seed workflow was subsequently run directly against the configured Atlas database. The deployed API verifier then completed successfully against those Atlas records: health and readiness checks passed, the seeded admin/doctor/nurse/patient accounts authenticated, patient-to-admin authorization was rejected, a live token progressed through call/start/complete, nurse vitals were persisted, analytics returned seeded data, and an authenticated patient WebSocket received `TOKEN_CANCELLED`.

The deployed frontend role selector and the dedicated doctor sign-in route were also loaded successfully from the public Render site, confirming the UI exposes the live role-aware authentication entry points rather than browser-only preview data.

The public doctor sign-in form accepted the seeded clinician credentials and issued the live backend authentication request. The resulting role dashboard response is being observed as part of the same production smoke test.

The seeded doctor successfully reached the deployed live dashboard, which displayed the remaining Atlas-backed waiting token. A dashboard-level `Call next` action was then issued to verify that the browser UI drives the real queue service rather than a local preview.

The browser refreshed to show that same token as `CALLED`, confirming the doctor dashboard action persisted through the deployed API and Atlas database. A direct post-action invariant check then confirmed zero broken seeded token relationships, zero duplicate active patient/day records, zero duplicate current doctor/day records, and zero queue-state length mismatches.
