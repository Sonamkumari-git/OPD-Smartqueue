# Render Deployment Verification

This deployment was verified after the Render Blueprint built commit `67fe728`.

| Surface | Verification result |
| --- | --- |
| Static frontend | The public root responds with HTTP 200. |
| Frontend assets | The hero, patient preview, logo, and texture assets respond with HTTP 200 from the published static site. |
| API health | `GET /health` responds with HTTP 200. |
| Database readiness | `GET /ready` responds with HTTP 200 and confirms the production database is ready. |
| Production logs | The API reported successful MongoDB connection, index verification, startup completion, and live health probes. |

## Deployment Repair Notes

The original static-site build invoked Corepack and failed during its package-manager signature verification. The Render build command now uses the pinned `pnpm@10.4.1` through `npx`, which bypasses that Corepack failure while preserving the frozen lockfile installation.

The UI originally referenced preview-only `/manus-storage/` asset paths. The existing compressed visual assets are now included in the static build under `/queue-assets/`, so the external Render domain serves them directly.

## Operational Note

The API is running on a free Render instance. It can spin down after inactivity, so its first request after an idle period may take longer than normal. The health endpoints remain the appropriate deployment probes:

```text
GET /health
GET /ready
```
