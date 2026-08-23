# Tab-Scoped Role Sessions

The application stores the authenticated user and bearer token in `sessionStorage`, not `localStorage`.

`localStorage` is shared by every tab from the same website, so signing into Doctor access in one tab could overwrite an open Patient session in another. `sessionStorage` is scoped to a single browser tab. A patient and a doctor can now remain signed in concurrently in separate tabs, each retaining the correct role-specific dashboard on refresh.

The legacy shared session key is cleared when the updated application loads. Users need to sign in again once after this change; after that, each tab maintains its own session until that tab is closed or the user signs out.
