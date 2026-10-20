# Módulos de administración

Pantallas de gestión que acompañan al espacio de órdenes: clientes, catálogo y tarifarios.

## Alcance actual

| Módulo | Listado | Alta | Edición / baja |
|---|---|---|---|
| Pacientes | Sí, con búsqueda por nombre o DNI | Sí | No |
| Clientes | Sí, con búsqueda por nombre o contacto | Sí | No |
| Catálogo · Exámenes | Sí, con búsqueda por código o nombre | Sí | No |
| Catálogo · Paquetes | Sí, con recuento de exámenes | Sí, con selección de exámenes | No |
| Tarifarios · Exámenes | Sí, con búsqueda | Sí | No |
| Tarifarios · Paquetes | Sí, con búsqueda | Sí | No |

Las altas usan los endpoints existentes del CRUD (`/api/pacientes/`, `/api/clientes/`, `/api/examenes/`) y los nuevos endpoints de solo alta y consulta para tarifas (`/api/tarifario-examenes/`, `/api/tarifario-paquetes/`).

## Límites conocidos

- **Paquetes**: el alta envía la composición completa en una sola petición y el backend la guarda de forma atómica. La lista de exámenes define el orden de visualización; un examen repetido o inexistente devuelve `400`. La edición de la composición existe en la API (`PATCH /api/paquetes/<id>/` con `examenes`), pero todavía no está expuesta en la interfaz.
- **Tarifarios**: las tarifas se agregan pero no se editan ni se dan de baja desde la interfaz. Una tarifa nueva participa en la cotización de órdenes posteriores; las órdenes ya guardadas recalculan su total con las tarifas vigentes, porque el precio no se congela por ítem.
- **Clientes y pacientes**: la edición y la baja tampoco están expuestas en la interfaz.

## Verificación

```bash
# Backend
cd backend
..\.venv\Scripts\python.exe -m pytest -q

# Frontend
cd frontend
npm run build
npm run lint

# Navegador
cd qa/e2e
npx playwright test --reporter=line
```

Las pruebas de navegador interceptan `/api/` con mock de respuestas; no requieren backend levantado.
