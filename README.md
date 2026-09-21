# LabCore — Sistema de gestión para laboratorio clínico

Aplicación web para un laboratorio clínico: registro de pacientes y clientes,
catálogo de exámenes y paquetes, órdenes con estados, captura de resultados
(manual e importación CSV de analizadores), reportes PDF y facturación.

> Repositorio **de código**. La documentación del proyecto vive en un
> repositorio privado separado. No subir datos reales de pacientes ni tarifas.

## Stack

- Backend: **Django 5** (Python 3.12+)
- Base de datos: **PostgreSQL** (SQLite para desarrollo local)
- PDF: WeasyPrint + QR (pendiente de implementar)
- Despliegue: Docker Compose en VPS + nginx/Caddy con HTTPS

## Estructura

```
src/
├── config/            # Settings, urls, wsgi/asgi
├── accounts/          # Usuario y roles (admin, encargada, auxiliar, reportes, muestreo)
├── catalogo/          # Zonas, clientes, exámenes, paquetes, tarifarios
├── pacientes/         # Pacientes (vinculados a clientes)
├── ordenes/           # Órdenes, items, estados y cálculo de tarifa
├── facturacion/       # Pagos
├── reportes/          # Reportes (nº correlativo, QR, entrega)
└── core/              # Bitácora de auditoría
```

## Inicio rápido (desarrollo)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
cd src
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Panel: `http://127.0.0.1:8000/admin/`

## Seguridad

- `DEBUG=False` y `ALLOWED_HOSTS` restringidos en producción.
- Secretos únicamente en `.env` (nunca en git).
- HTTPS obligatorio; respaldo diario cifrado fuera de sitio.