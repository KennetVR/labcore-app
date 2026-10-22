# Facturación y pagos

Registro de los pagos de las órdenes, saldo pendiente y estado de cuenta por cliente.

## Endpoints

| Método | Ruta | Quién | Efecto |
|---|---|---|---|
| `GET` | `/api/pagos/` | Autenticado | Lista paginada de pagos |
| `POST` | `/api/pagos/` | `admin`, `encargada`, `reportes` | Registra un pago |
| `GET` | `/api/pagos/<id>/` | Autenticado | Detalle de un pago |
| `POST` | `/api/pagos/<id>/anular/` | `admin`, `encargada`, `reportes` | Anula el pago con un motivo |
| `GET` | `/api/pagos/estado-cuenta/` | Autenticado | Resumen por cliente: facturado, pagado y saldo |

El detalle de la orden incluye `total_pagado`, `saldo` y la lista `pagos`.

## Registrar un pago

```json
POST /api/pagos/
{ "orden": 12, "monto": "35.00", "forma_pago": "contado", "observacion": "Abono" }
```

Formas de pago: `contado`, `boleta`, `factura`.

Reglas:
- El monto debe ser mayor a cero.
- La orden debe tener total: sin tarifa vigente no se puede cobrar.
- El monto no puede superar el saldo pendiente de la orden.
- Se admiten pagos parciales: varios pagos pueden cubrir la orden entre todos.
- El pago registra quién lo hizo (`registrado_por`) y cuándo (`fecha`).

## Saldo pendiente

- `saldo` = total de la orden − suma de los pagos **no anulados**.
- `saldo` es `null` cuando la orden no tiene total, y `0` cuando está cubierta.
- El saldo se recalcula con el total vigente de la orden, igual que el total que ya muestra el sistema. Si cambia una tarifa, cambia el saldo de las órdenes abiertas.

## Pagos inmutables y anulación

Un pago **no se edita ni se borra**: `PUT` y `PATCH` sobre `/api/pagos/<id>/` devuelven `405` y `DELETE` también. Para corregir un pago mal registrado se anula:

```json
POST /api/pagos/<id>/anular/
{ "motivo": "Monto mal tipeado" }
```

- El motivo es obligatorio; sin él la API responde `400`.
- Un pago ya anulado no se anula otra vez: `400`.
- La anulación guarda `anulado`, `anulado_por`, `anulado_at` y el motivo, que queda visible en el historial.
- Un pago anulado no cuenta para el saldo, pero sigue apareciendo en el listado.

## Consulta y filtros

`GET /api/pagos/` acepta:

| Parámetro | Efecto |
|---|---|
| `cliente=<id>` | Solo pagos de las órdenes de ese cliente |
| `orden=<id>` | Solo pagos de esa orden |
| `forma_pago=<valor>` | Solo esa forma de pago |
| `anulado=true` \| `false` | Solo anulados o solo vigentes |
| `search=<texto>` | Número de orden, nombre del cliente u observación |

## Estado de cuenta

`GET /api/pagos/estado-cuenta/` devuelve una fila por cliente con `facturado`, `pagado` y `saldo`.

- `facturado` suma los totales de las órdenes del cliente; las órdenes sin total no aportan.
- `pagado` suma los pagos no anulados de esas órdenes.
- Las órdenes de paciente particular se agrupan bajo `Particular`.

## Límites conocidos

- El estado de cuenta recalcula el total de cada orden, por lo que su costo crece con el número de órdenes.
- No hay comprobante de pago ni serie de numeración: el modelo `Pago` no los contempla todavía.
- No se registra la anulación en una bitácora: solo queda el motivo y el usuario.

## Verificación

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/test_pagos.py -q

cd ../qa/e2e
npx playwright test tests/payments.spec.ts --reporter=line
```
