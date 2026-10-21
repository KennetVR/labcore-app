# Facturación y pagos

Objetivo: cerrar el ciclo económico del laboratorio — de la orden cobrada al estado de cuenta por cliente — sobre el modelo `Pago` que ya existe en `backend/facturacion/models.py` pero que nunca tuvo API ni pantalla.

Rama: `feat/facturacion-pagos` · Estrategia de entrega: un commit por unidad de trabajo, luego PR a `main`.
Runner: `backend` → `..\.venv\Scripts\python.exe -m pytest`; `qa/e2e` → `npx playwright test --reporter=line`; `frontend` → `npm run lint` y `npm run build`.

## Specs

### S1 — Registrar pagos de una orden

El laboratorio debe poder registrar el pago de una orden con monto, forma de pago y observación.

- `POST /api/pagos/` con `{ "orden": <id>, "monto": "35.00", "forma_pago": "contado", "observacion": "" }`.
- Formas de pago: `contado`, `boleta`, `factura` (las del modelo `Pago.FormaPago`).
- El pago queda asociado a la orden y registra quién lo hizo (`registrado_por`) y cuándo (`fecha`).
- Un pago de `0` o negativo devuelve `400`.
- Una orden sin total (sin tarifa vigente) no admite pagos: devuelve `400`.
- Un pago que supera el saldo pendiente devuelve `400`.

### S2 — Saldo pendiente por orden

Cada orden debe mostrar cuánto se ha cobrado y cuánto falta.

- El saldo es el total de la orden menos la suma de los pagos no anulados.
- Se expone en el detalle de la orden como `total_pagado` y `saldo`.
- `saldo` es `null` cuando la orden no tiene total; `0` cuando está cubierta.
- El saldo se recalcula con el total vigente de la orden, igual que el total que ya muestra el sistema.

### S3 — Pagos inmutables, con anulación explícita

Ante la pregunta "¿Si el laboratorio registra un pago con el monto equivocado, ¿cómo se corrige?" la respuesta elegida fue: **"Inmutables, con anulación explícita (Recomendada)"**.

- Un pago no se edita ni se borra: `PUT` y `PATCH` sobre `/api/pagos/<id>/` devuelven `405`.
- La corrección es `POST /api/pagos/<id>/anular/` con `{ "motivo": "..." }`.
- El motivo es obligatorio: sin él, `400`.
- Un pago ya anulado no se anula otra vez: `400`.
- La anulación registra `anulado`, `anulado_por` y `anulado_at`, y el motivo queda visible.
- Un pago anulado no cuenta para el saldo, pero sigue visible en el historial.

### S4 — Estado de cuenta por cliente

- `GET /api/pagos/estado-cuenta/` devuelve una fila por cliente con `facturado`, `pagado` y `saldo`.
- `facturado` suma los totales de las órdenes del cliente; `pagado` suma sus pagos no anulados.
- Las órdenes sin total no aportan a `facturado`.
- Las órdenes de paciente particular se agrupan bajo `Particular`.

### S5 — Permisos por rol

- `admin`, `encargada` y `reportes` pueden registrar y anular pagos. El rol `reportes` es "Asistente de reportes/facturación" (`backend/accounts/models.py:10`).
- `auxiliar` y `muestreo` no pueden: `403`.
- Sin sesión: `403` en lectura y escritura.

### S6 — Consulta de pagos

- `GET /api/pagos/` lista los pagos paginados con `orden_numero`, `orden_total`, `orden_cliente`, `registrado_por_nombre`, `anulado_por_nombre` y el saldo de la orden.
- Filtros por query param: `cliente`, `orden`, `forma_pago`, `anulado` (`true`/`false`).
- La búsqueda textual cubre número de orden, nombre del cliente y observación.

## Tasks

| ID | Specs | Ruta | Estado | Commit |
|---|---|---|---|---|
| T1 | S1, S2, S3, S4, S5, S6 | inline (backend) | hecho | `921237e feat(api): pagos, saldo pendiente y anulacion` |
| T2 | S1, S2, S3, S4 | inline (frontend) | hecho | `7f57822 feat(web): pantalla de pagos, saldo y estado de cuenta` |
| T3 | S1–S6 | inline (docs) | hecho (docs/facturacion.md en T1) | — |

T1: modelo `Pago` con anulación, serializer, `PagoViewSet` con acción `anular` y `estado-cuenta`, saldo en el serializer de orden, tests backend.
T2: pantalla de Pagos con listado, filtros y estado de cuenta; sección de pagos en el detalle de orden; tests E2E.
T3: `docs/facturacion.md`.

## Log

- L1 (2026-10-21) — "ok sigamos con otra funcionalidad"
- L1 (2026-10-21) — Opción elegida entre las tres funcionalidades anunciadas y nunca implementadas: **"Facturación y pagos (Recomendada)"**.
- L1 (2026-10-21) — Decisión de corrección de pagos: **"Inmutables, con anulación explícita (Recomendada)"**.
- Decisión tomada: el saldo se calcula contra el total vigente de la orden, igual que el total que ya muestra el sistema. Congelar el precio de la orden es otra funcionalidad, no parte de esta.
- Decisión tomada: `admin`, `encargada` y `reportes` registran y anulan pagos; `auxiliar` y `muestreo` no.
- 2026-10-21 — Se integró `feat/banderas-automaticas` en esta rama (`1d0b831`): la DB local tenía la migración `ordenes.0002` aplicada y, sin el modelo en la rama, la tabla quedaba desalineada. Las dos features tocan tablas distintas, así que no hubo conflicto de migración.
- Evidencia: 22 pruebas backend nuevas (T1), 5 E2E nuevos (T2), 38/38 comprobaciones live de API y 10/10 en navegador real contra el stack vivo.
