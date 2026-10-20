# Quote an order before saving

Authenticated clients can `POST /api/ordenes/cotizar/` with the same JSON draft
accepted by `POST /api/ordenes/`. Both endpoints require session cookies and CSRF.
Quoting never saves an order or its items.

Example draft:

```json
{"cliente": 1, "paciente": 1, "items": [{"examen": 1, "cantidad": 2}]}
```

A successful quote returns ordered line prices and a total as decimal strings:

```json
{"items": [{"precio_unitario": "12.50", "subtotal": "25.00"}], "total": "25.00"}
```

IDs and amounts above are examples, not seeded prices. Missing applicable tariffs
return HTTP 400 with position-aligned `items` errors, just as creation does. An
explicit zero-price tariff is valid; absence of a tariff is not a zero price.

Each package is one billable row with `paquete` and the existing required `examen`
reference. The UI must choose that exam from the package's members. Do not expand
all package members into billable rows: each would charge the entire package.

Quote and creation use the same serializer validation and domain tariff lookup.
A quote does not reserve prices: changes to tariffs before submission can change
the saved total. Creation validates again. Existing historical totals are dynamic;
this feature does not add immutable price snapshots or alter tariff precedence.
Creation of the order and its items is atomic: an item-save failure rolls back
the parent order as well. Empty drafts retain the existing API behavior (zero
total); the UI should require at least one item before submission.

Run `..\.venv\Scripts\python.exe -m pytest tests/test_quote.py -q` from `backend`.
