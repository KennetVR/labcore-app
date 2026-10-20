import { expect, test } from '@playwright/test'

test('list clients and register a new one', async ({ page }) => {
  let created = false
  const client = { id: 3, nombre: 'Clinica Nueva', tipo: 'clinica', zona: 1, contacto: '999 888 777', activo: true }
  await page.route(/\/api\/(auth|clientes|zonas)\//, async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 1, username: 'qa', name: 'QA', role: 'auxiliar' }, csrf_token: 'test' } })
    }
    if (path === '/api/clientes/' && route.request().method() === 'POST') {
      expect(route.request().postDataJSON()).toEqual({
        nombre: 'Clinica Nueva', tipo: 'clinica', zona: 1, contacto: '999 888 777', activo: true,
      })
      created = true
      return route.fulfill({ status: 201, json: client })
    }
    const records: Record<string, unknown[]> = {
      '/api/clientes/': created ? [client] : [],
      '/api/zonas/': [{ id: 1, nombre: 'Lima Norte', activo: true }],
    }
    const results = records[path] ?? []
    await route.fulfill({ json: { count: results.length, next: null, previous: null, results } })
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Clientes', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Clientes', exact: true })).toBeVisible()
  await expect(page.getByText('No hay clientes para mostrar.')).toBeVisible()

  await page.getByRole('button', { name: 'Nuevo cliente' }).click()
  await page.getByLabel('Nombre', { exact: true }).fill('Clinica Nueva')
  await page.getByLabel('Tipo').selectOption('clinica')
  await page.getByLabel('Zona').selectOption('1')
  await page.getByLabel('Contacto').fill('999 888 777')
  await page.getByRole('button', { name: 'Guardar cliente' }).click()

  await expect(page.getByText('Clinica Nueva')).toBeVisible()
  await expect(page.getByText('Lima Norte')).toBeVisible()
})
