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

## Bandera automática por rango de referencia

Al guardar resultados, el backend compara cada valor con el rango de referencia del examen (`ref_min` y `ref_max` del catálogo) y guarda la bandera calculada:

| Situación | Bandera guardada | `rango_estado` |
|---|---|---|
| Por encima de `ref_max` | `H` | `alto` |
| Por debajo de `ref_min` | `L` | `bajo` |
| Dentro del rango | *(vacía)* | `normal` |
| Sin rango, resultado de texto o resultado no numérico | la que envía el laboratorio | `sin_rango` |

- El cálculo solo aplica a exámenes de tipo `numerico` con al menos un límite cargado.
- Se aceptan números con punto decimal (`95.5`) o coma decimal (`13,8`). Un resultado con unidades, operadores o texto (`Negativo`, `<0.5`, `95 mg/dL`) no es comparable y no produce bandera.
- Un rango con un solo límite también funciona: con `ref_min` se detecta el valor bajo, con `ref_max` el valor alto.
- **La bandera manual del laboratorio tiene prioridad**: si el item se envía con `bandera_manual: true`, el sistema guarda ese valor y no lo reemplaza. El item recuerda ese origen (`bandera_manual`) para que un guardado posterior no lo pise.
- Los rangos se cargan y editan en la pantalla de **Catálogo · Exámenes** (campos Mínimo y Máximo), o por API en `/api/examenes/`.

La respuesta incluye, por cada ítem, `bandera_calculada`, `rango_estado`, `unidad`, `ref_min`, `ref_max` y `ref_texto`, para que la interfaz muestre el rango junto al resultado.

## Límites conocidos

- Un paquete se captura por sus exámenes componentes, no como un resultado único.
- La bandera solo distingue alto y bajo: no distingue valores críticos dentro ni fuera del rango.
- La generación de PDF y el envío al paciente se documentan en `docs/reports.md`.

## Verificación

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/test_results.py tests/test_banderas.py -q

cd ../qa/e2e
npx playwright test tests/results.spec.ts tests/flags.spec.ts --reporter=line
```
