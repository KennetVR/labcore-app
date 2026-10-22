import { test, expect } from '@playwright/test'

test('pending save cannot discard a later draft', async ({ page }) => {
  let release!: () => void
  const gate = new Promise<void>(r => { release = r })
  await page.route(/\/api\/(auth|ordenes|pacientes|clientes|examenes|paquetes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    if (path.includes('/auth/')) return route.fulfill({ json: {
      user: { id: 1, name: 'QA', role: 'encargada' }, csrf_token: 'test',
    } })
    if (path.endsWith('/cotizar/')) return route.fulfill({ json: {
      items: [{ precio_unitario: '1.00', subtotal: '1.00' }], total: '1.00',
    } })
    if (route.request().method() === 'POST') {
      await gate
      return route.fulfill({ status: 201, json: { id: 1 } })
    }
    const records: Record<string, unknown[]> = {
      '/api/pacientes/': [{ id: 1, nombre_completo: 'Patient' }],
      '/api/examenes/': [{ id: 1, codigo: 'E', nombre: 'Exam', activo: true }],
    }
    const results = records[path] ?? []
    await route.fulfill({ json: { results, count: results.length, next: null } })
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Nueva orden' }).click()
  await page.getByRole('combobox', { name: 'Paciente', exact: true }).selectOption('1')
  await page.getByRole('combobox', { name: 'Examen o paquete' }).selectOption('e:1')
  await page.getByRole('button', { name: 'Agregar', exact: true }).click()
  await page.getByRole('button', { name: 'Cotizar', exact: true }).click()
  await page.getByRole('button', { name: 'Guardar orden' }).click()
  await expect(page.getByRole('button', { name: 'Guardar orden' })).toBeDisabled()
  await page.getByRole('button', { name: 'Órdenes', exact: true }).click()
  await page.getByRole('button', { name: 'Nueva orden' }).click()
  await page.getByLabel('Observación').fill('Preserve this draft')
  const saved = page.waitForResponse(r => r.request().method() === 'POST' && r.url().endsWith('/api/ordenes/'))
  release()
  await saved
  await expect(page.getByLabel('Observación')).toHaveValue('Preserve this draft')
})
