# Administración del laboratorio

Objetivo: completar las pantallas de gestión que acompañan al espacio de órdenes.
Rama: `feat/package-composition` (cadena de PRs #9–#13). Runner: pytest + Playwright.

## Specs

- **S1**: «despues de que hagas pr continua con lo demas» autoriza continuar con los módulos de administración restantes tras el PR de pacientes.
- **S2**: Pacientes: listado con búsqueda y alta; apellidos y nombres obligatorios; DNI, sexo, fecha de nacimiento, cliente y observaciones opcionales; un DNI repetido devuelve el error de la API y el formulario queda abierto.
- **S3**: Clientes: listado con búsqueda y alta; nombre obligatorio; tipo, zona, contacto y estado activo; sin zona se muestra «Sin zona».
- **S4**: Catálogo: pestañas Exámenes y Paquetes; alta de exámenes con código, nombre, área, tipo de resultado, unidad, método, rango y bandera pre/post; alta de paquetes con nombre, frecuencia y selección de exámenes; la lista define el orden y un paquete requiere al menos un examen.
- **S5**: Tarifarios: pestañas Exámenes y Paquetes; alta de precios con alcance por zona, cliente o general, vigencia y estado; la cotización existente no cambia.
- **S6**: Se conservan los datos demo, la resolución de precios, los permisos por rol y los contratos de lectura existentes (`examenes` de paquete sigue siendo `[{orden, examen}]`).

## Tasks

| ID | Spec | Ruta | Estado | Commit |
|---|---|---|---|---|
| T1 | S2 | inline | hecho | `02aec9e` (#9) |
| T2 | S3 | inline | hecho | `11d5e3a` (#10) |
| T3 | S4 | inline | hecho | `a9307cf` (#11) |
| T4 | S5 | inline | hecho | `275a15a` (#12) |
| T5 | S4, S6 | inline | hecho | `59af6f9` (#13) |

## Log

- **L1** (usuario): «despues de que hagas pr continua con lo demas»
- **L2**: PR #9 de pacientes abierto sobre `main`; el resto de la cadena se apila sobre la rama anterior.
- **L3**: Decisiones de alcance: las pantallas usan el CRUD existente; solo los tarifarios requieren endpoints nuevos. La edición y la baja quedan fuera por no estar pedidas.
- **L4**: La API de paquetes solo permitía leer `examenes`; se agregó escritura anidada con validación de ids, rechazo de repetidos e inexistentes y guardado atómico.
- **L5**: Evidencia: `pytest -q` completo sin fallos; `npm run build` y `npm run lint` limpios; 9 pruebas Playwright en verde.
- **L6**: Límites documentados en `docs/admin-modules.md`: sin edición ni baja en la interfaz, y los precios de órdenes guardadas se recalculan con las tarifas vigentes.
