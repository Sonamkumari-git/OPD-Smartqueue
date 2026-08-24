# Nurse Vitals Save and History Repair

The nurse vital `POST /api/vitals` persistence request succeeded for the selected active visit. The dashboard then refreshed the permitted vitals history with `GET /api/vitals/{patient_id}`, which failed with HTTP 500.

The Render traceback identified the cause: the nurse history authorization route attempted to call `queue_date()` on `QueueRepository`, which does not provide that method. The route now uses the canonical `QueueService.queue_date()` helper, and an integration regression test covers nurse recording plus retrieving vital history for an assigned active visit.

Revision `dca95c6` has been pushed to the Render-managed backend deployment queue. The public workflow verifier will be re-run after that revision is live.

The public verification completed successfully after deployment. The existing nurse recorded a new observation for active token `C-001`, and the follow-up vital-history request returned the persisted record with the expected patient relationship. This confirms the dashboard’s save-and-refresh sequence now works against Atlas-backed data.
