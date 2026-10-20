# Módulos de administración

Pantallas de gestión que acompañan al espacio de órdenes: clientes, catálogo y tarifarios.

## Alcance actual

| Módulo | Listado | Alta | Edición / baja |
|---|---|---|---|
| Pacientes | Sí, con búsqueda por nombre o DNI | Sí | Sí |
| Clientes | Sí, con búsqueda por nombre o contacto | Sí | Sí |
| Catálogo · Exámenes | Sí, con búsqueda por código o nombre | Sí | Sí |
| Catálogo · Paquetes | Sí, con recuento de exámenes | Sí, con selección de exámenes | Sí |
| Tarifarios · Exámenes | Sí, con búsqueda | Sí | Sí |
| Tarifarios · Paquetes | Sí, con búsqueda | Sí | Sí |

Las pantallas usan el CRUD existente (`/api/pacientes/`, `/api/clientes/`, `/api/examenes/`, `/api/paquetes/`) y los endpoints de tarifas (`/api/tarifario-examenes/`, `/api/tarifario-paquetes/`). La edición envía `PATCH` y la baja `DELETE` con confirmación previa.

## Límites conocidos

- **Bajas protegidas**: si un registro está en uso, la API responde `409 Conflict` con un mensaje y la interfaz lo muestra sin cerrar la pantalla. Ocurre, por ejemplo, al intentar borrar un paciente o cliente con órdenes, una zona con clientes o un examen usado en una orden.
- **Paquetes**: el alta y la edición envían la composición completa en una sola petición y el backend la guarda de forma atómica. La lista de exámenes define el orden de visualización; un examen repetido o inexistente devuelve `400`.
- **Tarifarios**: una tarifa nueva participa en la cotización de órdenes posteriores; las órdenes ya guardadas recalculan su total con las tarifas vigentes, porque el precio no se congela por ítem.

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
