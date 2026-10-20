# Resultados de órdenes

Captura y validación de resultados por ítem desde el detalle de la orden.

## Endpoints

| Método | Ruta | Quién | Efecto |
|---|---|---|---|
| `POST` | `/api/ordenes/<id>/resultados/` | Cualquier usuario autenticado | Guarda `resultado` y `bandera` de los ítems enviados |
| `POST` | `/api/ordenes/<id>/validar/` | `admin` y `encargada` | Marca todos los ítems como validados y cierra la captura |

Cuerpo de `resultados/`:

```json
{ "items": [{ "id": 1, "resultado": "95", "bandera": "" }] }
```

## Reglas

- Solo se aceptan ítems que pertenecen a la orden; cualquier id ajeno devuelve `400` y no guarda nada.
- `resultado` admite hasta 100 caracteres y `bandera` hasta 5.
- La orden pasa a **En proceso** cuando al menos un ítem tiene resultado y a **Con resultados** cuando todos lo tienen.
- Una orden **Validada**, **PDF generado** o **Entregada** no admite cambios de resultados (`400`).
- Validar exige que todos los ítems tengan resultado; si falta alguno devuelve `400`.
- Validar deja `validado_por` y `validado_at` en cada ítem.
- La orden no retrocede de estado si se borra un resultado: solo avanza.

## Límites conocidos

- Los resultados son texto libre; no se valida contra `ref_min`, `ref_max` ni se calcula la bandera automáticamente.
- Un paquete se captura por sus exámenes componentes, no como un resultado único.
- La generación de PDF y el envío al paciente todavía no están implementados.

## Verificación

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest -q

cd ../qa/e2e
npx playwright test tests/results.spec.ts --reporter=line
```
