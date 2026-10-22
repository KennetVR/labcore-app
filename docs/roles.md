# Roles y permisos

LabCore tiene exactamente dos roles. El token que se guarda en `Usuario.rol` es
`admin` o `encargada`; la interfaz muestra las etiquetas **Administrador** y
**Encargado**.

| Área | Encargado (`encargada`) | Administrador (`admin`) |
|---|---|---|
| Pacientes | Ver, registrar y editar | Todo lo anterior y eliminar |
| Clientes | Ver, registrar y editar | Todo lo anterior y eliminar |
| Catálogo (exámenes, paquetes, zonas) | Ver | Crear, editar y eliminar |
| Tarifarios | Ver | Crear, editar y eliminar |
| Órdenes | Ver, crear y editar antes de validar | Todo lo anterior y eliminar órdenes sin actividad |
| Resultados | Capturar y validar | Capturar y validar |
| Reportes | Generar, entregar, reenviar y ver historial | Lo mismo |
| Pagos | Ver y registrar | Ver, registrar y anular |
| Reapertura de órdenes | No | Sí, con motivo y auditoría |
| Usuarios y bitácora (Django admin) | No | Sí |

## Reglas que ningún rol puede saltarse

- **El estado de la orden no se escribe por la API.** Solo cambia con las
  acciones del flujo (`resultados`, `validar`, `reporte`, `entrega`, `reabrir`).
  Enviar `estado` en un `POST` o `PATCH` devuelve `400`.
- **Los campos clínicos no se escriben al crear la orden.** `resultado`,
  `bandera` y `bandera_manual` solo se aceptan en `POST /api/ordenes/<id>/resultados/`.
  Enviarlos dentro de los ítems al crear devuelve `400`.
- **Los pagos son inmutables.** No se editan ni se borran (`405`). Para
  corregirlos se anulan con motivo, y solo el administrador puede hacerlo.
- **Una orden validada no se edita.** Para corregirla, el administrador la
  reabre: la orden vuelve a **Con resultados**, se limpian `validado_por` y
  `validado_at`, se exige volver a validar y queda un registro en `Bitacora`.
  No se reabre una orden con reporte generado.
- **Las bajas tienen guardas.** Un paciente o cliente con órdenes no se elimina
  (`409`), y una orden con pagos o ya validada tampoco (`400`).
- **Un rol fuera de la política falla cerrado.** Valores históricos como
  `auxiliar`, `reportes` o `muestreo` no reciben ninguna capacidad y la API
  responde `403`.

## Dónde se aplica

- **Backend (autoridad):** `backend/accounts/capacidades.py` define la matriz de
  capacidades y `backend/accounts/permisos.py` la aplica por método HTTP en cada
  viewset. Las acciones sensibles (`anular`, `reabrir`) validan la capacidad
  dentro de la acción.
- **Interfaz (espejo):** `frontend/src/api/permisos.ts` replica las capacidades
  para ocultar controles que el servidor rechazaría. Si cambia la política, el
  backend manda: primero se actualiza la matriz y después el espejo.
- **Django admin:** solo expone `Usuario` (gestión de identidades y rol) y
  `Bitacora` (solo lectura), y exige `rol == "admin"`. Los modelos de negocio se
  editan únicamente por la API de la aplicación.

## Cuentas existentes

La migración `accounts.0002_dos_roles` reasigna sin borrar usuarios ni historial:
`auxiliar`, `reportes` y `muestreo` pasan a `encargada`. Las cuentas con
`admin` se mantienen. El rol por defecto de un usuario nuevo es `encargada`.

## Verificación

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/test_permisos_api.py tests/test_permisos.py -q

cd ../qa/e2e
npx playwright test tests/payments.spec.ts --reporter=line
```
