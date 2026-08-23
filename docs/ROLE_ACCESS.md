# Role-Specific Access

The deployed application no longer creates client-side preview identities for patient, doctor, nurse, or administrator controls.

| Role | Entry route | Access rule | Destination after backend authentication |
| --- | --- | --- | --- |
| Patient | `/sign-in/patient` | May self-register, then sign in | `/dashboard/patient` |
| Doctor | `/sign-in/doctor` | Requires a provisioned doctor account | `/dashboard/doctor` |
| Nurse | `/sign-in/nurse` | Requires a provisioned nurse account | `/dashboard/nurse` |
| Administrator | `/sign-in/admin` | Requires a provisioned administrator account | `/dashboard/admin` |

Each role page sends credentials to the FastAPI authentication endpoint. The application checks that the returned account role matches the selected sign-in page. On a mismatch, it clears the session and directs the user to the matching role entry point. Dashboard routes are also guarded: an unauthenticated visitor is sent to the appropriate sign-in page, and an authenticated user cannot open a different role’s dashboard URL.

Local visual checks confirmed that the role-selection page and dedicated doctor sign-in page render as real credential forms, not preview dashboards.
