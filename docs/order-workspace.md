# Use the order workspace locally

Run the backend from `backend` with `..\.venv\Scripts\python.exe manage.py runserver 8000`.
Run `npm run dev` from `frontend`, then open `http://localhost:5174`.
Use an existing Django account; no password is embedded in the UI.

1. Sign in. Session credentials remain in Django cookies, never local storage.
2. Browse orders and filter by number/patient/client text, status, or exact date.
3. Select **Nueva orden**, an existing patient, and the appropriate client.
4. Add exams or packages. Each package is one billable line using its first member
   as the required exam reference. Packages without a resolvable member cannot be added.
5. Select **Cotizar**. Missing tariffs are displayed as errors, not zero prices.
6. Select **Guardar orden**. Editing any draft field invalidates the previous quote.

Orders without a calculated total display **Tarifa pendiente**. Explicit zero-price
tariffs remain valid. Quoting does not create an order; saving recalculates prices.
Errors leave the draft available for correction. A successful save returns to the list.

## Current boundary

This increment uses existing patients and clients. Their management remains in
Django admin. Result capture, PDF generation, role-specific navigation, tariff editing,
and historical price snapshots are not part of this screen.

The UI loads all API pages before applying local filters. This supports the current
small dataset, but server-side filtering and paginated rendering are future work
for larger installations. Do not treat this as a production-scale list implementation.
Session expiration is surfaced as an API error; reload the page to sign in again.

The Vite proxy preserves Host (`changeOrigin: false`) so Django's CSRF Origin check
works on the local same-origin `/api` URL. Production requires an appropriately
configured same-origin reverse proxy and HTTPS, not the Vite development server.

## Checks

- Backend: root venv Python, `-m pytest` from `backend`.
- Frontend: `npm run build` and `npm run lint` from `frontend`.
- Browser: `npx playwright test --reporter=line` from `qa/e2e`.
  The order workflow uses intercepted API responses and does not modify demo data.
  Backend tests separately verify real sessions, CSRF, tariff errors and rollback.
