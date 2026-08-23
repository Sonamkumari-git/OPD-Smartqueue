# Patient Registration Validation

The production FastAPI logs showed that the reported account-creation attempts reached `POST /api/auth/register` and were rejected with HTTP 422 validation responses. This confirms that the frontend-to-backend connection and CORS policy were functioning; the request data did not satisfy the registration contract.

The registration form now requires a full name of at least two characters and a password of at least eight characters before submission. It also trims the name and phone number and normalizes the email address. If any other backend validation rule rejects a request, the frontend now presents the first field-level FastAPI message instead of a generic request failure.

The FastAPI registration contract accepts a patient name, valid email address, optional phone number, and password with a minimum of eight characters.
