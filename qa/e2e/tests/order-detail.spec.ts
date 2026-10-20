import { expect, test } from '@playwright/test'

test('open an order detail and return to the list', async ({ page }) => {
  const order = {
    id: 1,
    numero: 'ORD-1',
    paciente_nombre: 'Demo Patient',
    cliente_nombre: 'Demo Clinic',
    fecha: '2026-10-20',
    estado: 'registrada',
    observacion: 'Ayuno de 8 horas',
    solicitado_por: 'Dra. Ruiz',
    total: '30.00',
    items: [
      {
        id: 1,
        examen: 9,
        examen_codigo: 'HB',
        examen_nombre: 'Hemoglobina',
        paquete: 4,
        paquete_nombre: 'Control Mensual',
        cantidad: 2,
        medicion: 'unica',
        resultado: '',
        bandera: '',
      },
    ],
  }
  await page.route(/\/api\/(auth|ordenes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 1, username: 'qa', name: 'QA', role: 'auxiliar' }, csrf_token: 'test' } })
    }
    if (path === '/api/ordenes/1/') return route.fulfill({ json: order })
    const results = path === '/api/ordenes/' ? [{ id: 1, numero: 'ORD-1', paciente_nombre: 'Demo Patient', cliente_nombre: 'Demo Clinic', fecha: '2026-10-20', estado: 'registrada', total: '30.00' }] : []
    await route.fulfill({ json: { count: results.length, next: null, previous: null, results } })
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Ver orden ORD-1', exact: true }).click()

  await expect(page.getByRole('heading', { name: 'ORD-1' })).toBeVisible()
  await expect(page.getByText('Hemoglobina')).toBeVisible()
  await expect(page.getByText('Control Mensual')).toBeVisible()
  await expect(page.getByText('Ayuno de 8 horas')).toBeVisible()

  await page.getByRole('button', { name: 'Volver al listado' }).click()
  await expect(page.getByRole('button', { name: 'Nueva orden' })).toBeVisible()
})
