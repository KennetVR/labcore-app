# QA — Pruebas

Carpeta dedicada al **agente de QA**. Las pruebas se dividen en dos niveles:

| Nivel | Herramienta | Dónde | Qué cubre |
|---|---|---|---|
| Unitarias / API | pytest + pytest-django | `backend/tests/` | Modelos, serializers, endpoints y reglas de negocio (validación doble, tarifas, estados) |
| E2E (frontend) | Playwright | `qa/e2e/` | Flujos del usuario en el navegador contra el frontend real |

## Pruebas de backend (pytest)

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

- Usa la BD de prueba de Django (no toca la de desarrollo).
- Cobertura mínima obligatoria en cada cambio: API CRUD, autenticación, cálculo
  de tarifas (`calcular_total`), flujo de estados de orden, importación CSV.

## Pruebas E2E (Playwright)

```powershell
cd qa/e2e
npm install
npx playwright install chromium
npx playwright test            # inicia el frontend y corre las pruebas
```

- Config: `qa/e2e/playwright.config.ts` (baseURL `http://localhost:5173`, inicia
  `npm run dev` del frontend automáticamente).
- Para E2E que use la API, levantar antes el backend:
  `cd backend` → `python manage.py runserver` y usar datos de prueba.

## Checklist de QA

- [ ] API responde 401/403 sin sesión
- [ ] Solo `encargada` puede validar/autotorizar resultados
- [ ] No se genera PDF sin orden validada
- [ ] `calcular_total` correcto con tarifario por zona/cliente y por vigencia
- [ ] CSV de analizador valida contra valores de referencia y reporta errores
- [ ] NNU Pre y Post aparecen ambos en el reporte
- [ ] Numeración correlativa de órdenes y reportes sin saltos
- [ ] Bitácora registra cambios de resultado y pagos
- [ ] Flujo completo E2E: registrar orden → resultados → validación → PDF → entrega