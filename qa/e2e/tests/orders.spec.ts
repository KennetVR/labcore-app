import { expect, test } from '@playwright/test'

test('sign in, quote a package once, invalidate stale quote, and save', async ({ page }) => {
  let signedIn = false
  let saved = false
  const user = { id: 1, username: 'qa', name: 'QA', role: 'auxiliar' }
  await page.route(/\/api\/(auth|ordenes|pacientes|clientes|examenes|paquetes)\//, async route => {
    const url = new URL(route.request().url())
    const path = url.pathname
    let body: unknown
    if (path === '/api/auth/session/') body = { user: signedIn ? user : null, csrf_token: 'token' }
    else if (path === '/api/auth/login/') {
      signedIn = true
      body = { user, csrf_token: 'fresh-token' }
    } else if (path === '/api/auth/logout/') body = { user: null, csrf_token: 'token' }
    else if (path === '/api/ordenes/cotizar/') {
      expect(route.request().headers()['x-csrftoken']).toBe('fresh-token')
      expect(route.request().postDataJSON().items).toEqual([
        { examen: 9, paquete: 4, cantidad: 1, medicion: 'unica' },
      ])
      body = { items: [{ precio_unitario: '30.00', subtotal: '30.00' }], total: '30.00' }
    } else if (path === '/api/ordenes/' && route.request().method() === 'POST') {
      saved = true
      body = { id: 1, numero: 'TEST001', total: '30.00' }
    } else {
      const records: Record<string, unknown[]> = {
        '/api/pacientes/': [{ id: 1, nombre_completo: 'Demo Patient', cliente: 2 }],
        '/api/clientes/': [{ id: 2, nombre: 'Demo Clinic' }],
        '/api/examenes/': [{ id: 9, codigo: 'HB', nombre: 'Hemoglobina', activo: true }],
        '/api/paquetes/': [{ id: 4, nombre: 'Monthly', activo: true, examenes: [{ orden: 1, examen: 9 }] }],
        '/api/ordenes/': saved ? [{ id: 1, numero: 'TEST001', paciente_nombre: 'Demo Patient', cliente_nombre: 'Demo Clinic', fecha: '2026-10-20', estado: 'registrada', total: '30.00' }] : [],
      }
      body = { count: records[path]?.length ?? 0, next: null, previous: null, results: records[path] ?? [] }
    }
    await route.fulfill({ json: body })
  })
  await page.goto('/')
  await page.getByLabel('Usuario').fill('qa')
  await page.getByLabel('Contraseña').fill('test-only')
  await page.getByRole('button', { name: 'Iniciar sesión' }).click()
  await page.getByRole('button', { name: 'Nueva orden' }).click()
  await page.getByRole('combobox', { name: 'Paciente', exact: true }).selectOption('1')
  await page.getByRole('combobox', { name: 'Examen o paquete', exact: true }).selectOption('p:4')
  await page.getByRole('button', { name: 'Agregar', exact: true }).click()
  await expect(page.getByRole('button', { name: 'Guardar orden' })).toBeDisabled()
  await page.getByRole('button', { name: 'Cotizar' }).click()
  await expect(page.getByRole('button', { name: 'Guardar orden' })).toBeEnabled()
  await page.getByLabel('Observación').fill('demo')
  await expect(page.getByRole('button', { name: 'Guardar orden' })).toBeDisabled()
  await page.getByRole('button', { name: 'Cotizar' }).click()
  await page.getByRole('button', { name: 'Guardar orden' }).click()
  await expect(page.getByText('TEST001', { exact: true })).toBeVisible()
})
