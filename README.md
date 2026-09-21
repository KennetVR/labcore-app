# LabCore — Sistema de gestión para laboratorio clínico

Aplicación web para un laboratorio clínico: registro de pacientes y clientes,
catálogo de exámenes y paquetes, órdenes con estados, captura de resultados
(manual e importación CSV de analizadores), reportes PDF y facturación.

> Repositorio **de código**. La documentación (plan, arquitectura, tarifario)
> vive en un repositorio privado separado. No subir datos reales de pacientes
> ni tarifas.

## Arquitectura

```
[Frontend React + Vite] ──HTTP/JSON──▶ [Backend Django + DRF] ──▶ [PostgreSQL]
        (SPA, puerto 5174)               (API REST, puerto 8000)
```

## Estructura por frentes (3 agentes en paralelo)

| Frente | Carpeta | Stack | Comandos |
|---|---|---|---|
| **Backend** | `backend/` | Django + Django REST Framework | `cd backend && python manage.py runserver` |
| **Frontend** | `frontend/` | React 18 + Vite + TypeScript | `cd frontend && npm install && npm run dev` |
| **QA** | `qa/` + `backend/tests/` | pytest (backend) + Playwright (E2E) | ver `qa/README.md` |

```
├── backend/               # API REST
│   ├── config/            # puerto 8000
│   ├── api/               # serializers, viewsets y rutas /api/*
│   ├── accounts/          # usuarios y roles
│   ├── catalogo/          # zonas, clientes, exámenes, paquetes, tarifarios
│   ├── pacientes/         # pacientes
│   ├── ordenes/           # órdenes, items, estados, cálculo de tarifa
│   ├── facturacion/       # pagos
│   ├── reportes/          # reportes PDF
│   ├── core/              # bitácora
│   └── tests/             # pytest (unitarias + API)
├── frontend/              # SPA React (puerto 5174)
│   └── src/api/           # cliente HTTP hacia /api
└── qa/
    └── e2e/               # Playwright (E2E del frontend)
```

## Inicio rápido (desarrollo)

### 1. Backend

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
cd backend
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

- Admin: `http://127.0.0.1:8000/admin/`
- API: `http://127.0.0.1:8000/api/` (requiere sesión)

### 2. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Abrir `http://localhost:5174` (el proxy reenvía `/api` → backend).

### 3. Pruebas

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest

cd ..\qa\e2e
npx playwright test
```

## Seguridad

- `DEBUG=False` y `ALLOWED_HOSTS` restringidos en producción; CORS solo para
  los orígenes indicados en `.env`.
- Secretos únicamente en `.env` (nunca en git).
- HTTPS obligatorio; respaldo diario cifrado fuera de sitio.