# Reporte PDF

Generación del informe de resultados en PDF para órdenes validadas, con código QR de verificación.

## Endpoints

| Método | Ruta | Quién | Efecto |
|---|---|---|---|
| `POST` | `/api/ordenes/<id>/reporte/` | `admin`, `encargada`, `reportes` | Genera el PDF y pasa la orden a **PDF generado** |
| `GET` | `/api/reportes/<id>/` | Autenticado | Metadatos del reporte |
| `GET` | `/api/reportes/<id>/pdf/` | Autenticado | Descarga el PDF adjunto |

El detalle de la orden incluye `reporte` con `id`, `numero`, `generado` y `pdf_url`; es `null` mientras no se haya generado.

## Reglas

- Solo se genera para órdenes en estado **Validada**. Cualquier otro estado devuelve `400`.
- La generación es idempotente: si ya existe un reporte, devuelve `200` con los mismos metadatos en lugar de crear otro.
- La generación es atómica: si falla la escritura del PDF, se borra la fila y el archivo, la orden queda en **Validada** y la API responde `500`; se puede reintentar.
- Los nombres de paciente y cliente se escapan antes de entrar al PDF, así que un `<` o `&` no rompe la generación.
- El PDF se arma con la identificación de la orden, el paciente, el cliente, la tabla de exámenes con resultado y bandera, el validador y un QR con el número de reporte.
- Al generarlo, la orden pasa a **PDF generado** y queda cerrada para captura (`400` en `resultados/`).
- Los archivos se guardan en `MEDIA_ROOT/reportes/<año>/<mes>/`.

## Dependencias

Se agregó `reportlab~=4.2` a `requirements.txt` para construir el PDF. El QR usa `qrcode` y `Pillow`, que ya estaban en el proyecto.

## Límites conocidos

- No hay envío por correo ni registro de entrega; los campos `enviado_a`, `entregado_at` y `entregado_por` del modelo quedan sin uso.
- El QR codifica el número de reporte; no hay URL pública de verificación.
- No se firma digitalmente el PDF.
- Regenerar un reporte no actualiza su contenido: si cambian los datos, hay que borrar el reporte en administración antes de volver a generarlo.

## Verificación

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/test_reports.py -q

cd ../qa/e2e
npx playwright test tests/reports.spec.ts --reporter=line
```

Las pruebas de backend comprueban el contenido real del archivo (`%PDF`), la idempotencia, los permisos y la descarga.
