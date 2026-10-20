import { expect, test } from '@playwright/test'

test('list tariffs and register an exam tariff', async ({ page }) => {
  let created = false
  const tariff = {
    id: 8, examen: 11, examen_codigo: 'HB', examen_nombre: 'Hemoglobina', precio: '15.00',
    zona: 1, zona_nombre: 'Lima Norte', cliente: null, cliente_nombre: null,
    vigencia_desde: null, activo: true,
  }
  await page.route(/\/api\/(auth|tarifario-examenes|tarifario-paquetes|examenes|paquetes|zonas|clientes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 1, username: 'qa', name: 'QA', role: 'auxiliar' }, csrf_token: 'test' } })
    }
    if (path === '/api/tarifario-examenes/' && route.request().method() === 'POST') {
      expect(route.request().postDataJSON()).toEqual({
        examen: 11, precio: '15', zona: 1, cliente: null, vigencia_desde: null, activo: true,
      })
      created = true
      return route.fulfill({ status: 201, json: tariff })
    }
    const records: Record<string, unknown[]> = {
      '/api/tarifario-examenes/': created ? [tariff] : [],
      '/api/tarifario-paquetes/': [{
        id: 9, paquete: 4, paquete_nombre: 'Control Mensual', precio: '45.00',
        zona: null, zona_nombre: null, cliente: null, cliente_nombre: null, vigencia_desde: null, activo: true,
      }],
      '/api/examenes/': [{ id: 11, codigo: 'HB', nombre: 'Hemoglobina' }],
      '/api/paquetes/': [{ id: 4, nombre: 'Control Mensual', frecuencia: 'mensual', activo: true, examenes: [] }],
      '/api/zonas/': [{ id: 1, nombre: 'Lima Norte', activo: true }],
      '/api/clientes/': [],
    }
    const results = records[path] ?? []
    await route.fulfill({ json: { count: results.length, next: null, previous: null, results } })
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Tarifarios', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Tarifarios', exact: true })).toBeVisible()
  await expect(page.getByText('No hay tarifas de exámenes.')).toBeVisible()

  await page.getByRole('button', { name: 'Nueva tarifa' }).click()
  await page.getByLabel('Examen').selectOption('11')
  await page.getByLabel('Precio').fill('15')
  await page.getByLabel('Zona').selectOption('1')
  await page.getByRole('button', { name: 'Guardar tarifa' }).click()

  await expect(page.getByText('HB - Hemoglobina')).toBeVisible()
  await expect(page.getByText('S/ 15.00')).toBeVisible()

  await page.getByRole('tab', { name: 'Paquetes' }).click()
  await expect(page.getByText('Control Mensual')).toBeVisible()
  await expect(page.getByText('S/ 45.00')).toBeVisible()
})
