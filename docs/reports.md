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

## Entrega

| Método | Ruta | Quién | Efecto |
|---|---|---|---|
| `POST` | `/api/ordenes/<id>/entrega/` | `admin`, `encargada`, `reportes` | Envía el PDF por correo (opcional) y registra la entrega |

Cuerpo: `{ "enviado_a": "paciente@correo.com" }`. El correo es opcional: vacío registra una entrega en mano.

Reglas:

- Requiere un reporte generado y la orden en **PDF generado**; si no, devuelve `400`.
- Con correo, envía el PDF adjunto como `<numero>.pdf`. Un correo inválido devuelve `400`.
- Si el envío falla, responde `502` y **no** registra la entrega; la orden queda en **PDF generado** para reintentar.
- La entrega es única y se apoya en `entregado_at`: repetirla devuelve `400` aunque alguien revierta el estado de la orden.
- Un cuerpo que no sea un objeto JSON devuelve `400`.
- Deja `enviado_a`, `entregado_at` y `entregado_por` en el reporte y pasa la orden a **Entregada**.
- El detalle de la orden expone esos tres campos dentro de `reporte`.

## Configuración de correo

`EMAIL_BACKEND` (por defecto `django.core.mail.backends.console.EmailBackend`, que imprime el mensaje en consola) y `DEFAULT_FROM_EMAIL` (`reportes@labcore.local` por defecto). En producción se configuran por entorno.

## Límites conocidos

- El QR codifica el número de reporte; no hay URL pública de verificación.
- No se firma digitalmente el PDF.
- Regenerar un reporte no actualiza su contenido: si cambian los datos, hay que borrar el reporte en administración antes de volver a generarlo.
- No hay reintento automático de correo ni historial de envíos: cada entrega se registra una sola vez.

## Verificación

```bash
cd backend
..\.venv\Scripts\python.exe -m pytest tests/test_reports.py tests/test_delivery.py -q

cd ../qa/e2e
npx playwright test tests/reports.spec.ts tests/delivery.spec.ts --reporter=line
```

Las pruebas de backend comprueban el contenido real del archivo (`%PDF`), la idempotencia, los permisos y la descarga.
