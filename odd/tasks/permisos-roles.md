# Permisos por rol

Objetivo: aplicar en todo el sistema la política de dos roles acordada con el usuario.
Rama: `feat/permisos-roles`. Runner: `pytest` (backend), Playwright (E2E) y `npm run build` / `npm run lint`.

## Specs

- **S1 — Dos roles.** Existen exactamente `admin` («Administrador») y `encargada` («Encargado»). Los valores `auxiliar`, `reportes` y `muestreo` dejan de existir. La migración reasigna esas cuentas a `encargada` sin borrar usuarios ni historial. Rol desconocido o ausente falla cerrado.
- **S2 — Encargado (operación diaria).** Registra y consulta pacientes y datos básicos de clientes; consulta catálogo, rangos y tarifas; crea y edita órdenes antes de validarlas; captura resultados; valida resultados; genera, entrega y reenvía reportes; registra pagos y consulta saldos y estado de cuenta.
- **S3 — Administrador.** Puede operar como el encargado y además: anular pagos, editar catálogo/rangos/tarifas, eliminar registros, autorizar la reapertura de órdenes validadas y gestionar usuarios.
- **S4 — Autoridad del servidor.** La política se aplica en todos los endpoints, incluido el CRUD genérico. Una acción sin capacidad responde `403` y no produce efectos.
- **S5 — Estados y datos clínicos.** `estado` de la orden no es escribible por la API; los valores `resultado`, `bandera` y `bandera_manual` no se aceptan al crear la orden. Solo la acción `resultados` los modifica.
- **S6 — Integridad clínica.** Una orden validada, con PDF o entregada no se edita. Solo el administrador puede reabrir una orden en estado `validada`, con motivo obligatorio, registro en `Bitacora` y nueva validación; si el reporte ya fue emitido, la reapertura se rechaza.
- **S7 — Dinero.** Los pagos se registran por ambos roles y solo el administrador los anula, con motivo. Siguen siendo inmutables: no se editan ni se borran.
- **S8 — Administrador de Django.** Solo expone `Usuario` (gestión de identidades) y `Bitacora` (solo lectura), ambos reservados al rol `admin`. Los modelos de negocio no se editan allí para no saltarse las reglas de la API.
- **S9 — Interfaz.** Menús y controles reflejan las capacidades: el encargado ve catálogo y tarifas en solo lectura, no ve eliminar, anular ni reabrir.
- **S10 — Pruebas.** Matriz rol × acción × estado, denegaciones sin efectos, paridad de la interfaz y actualización de la documentación.

## Tasks

| ID | Specs | Ruta | Estado | Evidencia |
| --- | --- | --- | --- | --- |
| T1 | S1 | inline | hecho | `accounts/capacidades.py`, `accounts/permisos.py`, `accounts/models.py`, migración `0002_dos_roles`; `makemigrations --check` sin cambios |
| T2 | S4–S8 | inline | hecho | permisos por método en todos los viewsets; `estado` y campos clínicos rechazados; anulación solo admin; `reabrir` auditado; admin de Django reducido a `Usuario` y `Bitacora` |
| T3 | S10 | inline | hecho | 220 pruebas backend en verde, incluida `tests/test_permisos_api.py` (30 casos); fixtures `usuario`=encargada y `administrador` |
| T4 | S9 | inline | hecho | `frontend/src/api/permisos.ts`; gating en pacientes, clientes, catálogo, tarifarios, pagos y detalle; reapertura admin con motivo |
| T5 | S10 | inline | hecho | 30 pruebas Playwright en verde; mocks de rol actualizados y caso «el encargado cobra pero no anula» |
| T6 | S2, S3, S7 | inline | hecho | `docs/roles.md` y actualización de facturación, reportes, resultados, sesión, módulos y QA |
| T7 | S10 | inline | en curso | `npm run build` y `npm run lint` en verde; migración aplicada a la base local |

## Log

- **L1 (original):** «acabo de revisar con cada rol pero parece que todos pueden hacer lo mismo, primo haz un plan de como y quien hara cada cosa»
- **L2:** «Aca solo hay 2 roles, el administrador y el encargado ya tu decide como arquitecto de software quien debe tener que permisos y demas»
- **L3:** «Bien ahora apliquemos esto»
- **L4 (evidencia):** el relevamiento de solo lectura encontró CRUD genérico autenticado para pacientes, clientes, catálogo, tarifas y órdenes; `estado` escribible; resultados aceptados anidados al crear; navegación sin gating; `admin` y `encargada` equivalentes en la práctica.
- **L5 (decisión):** `encargada` conserva su identificador persistido para no romper cuentas ni historial; solo cambia la etiqueta visible a «Encargado».
- **L6 (decisión):** las cuentas con roles eliminados pasan a `encargada` en la migración. Es la única reasignación automática y queda documentada; no se borra ningún usuario.
- **L7 (interfaz):** `permisos.ts` replica la matriz; el encargado ve catálogo y tarifarios sin botones de edición, no ve eliminar en pacientes/clientes, cobra sin anular y no ve «Reabrir para corregir». La reapertura pide motivo y solo aparece en `validada` sin reporte.
- **L8 (pruebas):** la suite backend pasó de 190 a 220 casos. Los mocks E2E dejaron de usar roles eliminados: editar configuración usa `admin`; operar usa `encargada`. Playwright: 30/30.
- **L9 (base local):** `accounts.0002_dos_roles` aplicada. `admin` sigue `admin`; `encargada` sigue `encargada`; la cuenta `reportes` pasó a `encargada`.
- **L10 (verificación):** `pytest` 220 pruebas, 0 fallos, 0 errores; `makemigrations --check` sin cambios; Playwright 30/30; `npm run build` y `npm run lint` en verde.
