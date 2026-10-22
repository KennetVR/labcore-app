import { expect, test } from '@playwright/test'

const items = [{ id: 1, examen: 11, examen_codigo: 'GLU', examen_nombre: 'Glucosa', paquete: null, paquete_nombre: '', cantidad: 1, medicion: 'unica', resultado: '95', bandera: '', validado_por: 9, validado_at: '2026-01-01T10:00:00Z' }]
const reporte = { id: 3, numero: 'R202601010001', generado: '2026-01-01T11:00:00Z', pdf_url: '/api/reportes/3/pdf/', enviado_a: 'first@example.com', entregado_at: '2026-01-01T12:00:00Z', entregado_por: 'Jefa' }
const history = [
  { id: 1, enviado_a: 'first@example.com', usuario: 'jefa', fecha: '2026-01-01T12:00:00Z', estado: 'enviado' as const, reenvio: false },
]
const baseOrder = {
  id: 5, numero: '202601010001', paciente_nombre: 'Perez, Ana', cliente_nombre: 'Particular',
  fecha: '2026-01-01', estado: 'entregada', total: '20.00', observacion: '', solicitado_por: '', items, reporte,
}

async function openOrder(page: import('@playwright/test').Page) {
  let sent = ''
  let currentHistory = [...history]
  await page.route(/\/api\/(auth|ordenes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    const method = route.request().method()
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 9, username: 'jefa', name: 'Jefa', role: 'encargada' }, csrf_token: 'test' } })
    }
    if (path === '/api/ordenes/5/envios/' || path.startsWith('/api/ordenes/5/envios?')) {
      return route.fulfill({ json: { count: currentHistory.length, next: null, previous: null, results: currentHistory } })
    }
    if (path === '/api/ordenes/5/reenviar/' && method === 'POST') {
      const body = route.request().postDataJSON() as { enviado_a: string; solicitud: string }
      sent = body.enviado_a
      const newEvent = { id: 2, enviado_a: body.enviado_a, usuario: 'jefa', fecha: '2026-01-01T13:00:00Z', estado: 'enviado' as const, reenvio: true }
      currentHistory = [newEvent, ...currentHistory]
      return route.fulfill({ json: newEvent })
    }
    if (path === '/api/ordenes/5/') return route.fulfill({ json: baseOrder })
    if (path === '/api/ordenes/') {
      return route.fulfill({ json: { count: 1, next: null, previous: null, results: [baseOrder] } })
    }
    return route.fulfill({ json: { count: 0, next: null, previous: null, results: [] } })
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Ver orden 202601010001' }).click()
  return () => sent
}

test('shows delivery history and allows resending to a new recipient', async ({ page }) => {
  const getSent = await openOrder(page)

  await expect(page.getByText('Historial de envíos')).toBeVisible()
  await expect(page.getByRole('cell', { name: 'first@example.com' })).toBeVisible()
  await expect(page.getByText('enviado')).toBeVisible()

  await page.getByLabel('Nuevo correo de entrega (opcional)').fill('second@example.com')
  await page.getByRole('button', { name: 'Reenviar por correo' }).click()

  await expect.poll(getSent).toBe('second@example.com')
  await expect(page.getByRole('cell', { name: 'second@example.com' })).toBeVisible()
})

test('resends in hand without email', async ({ page }) => {
  const getSent = await openOrder(page)

  await page.getByRole('button', { name: 'Reenviar en mano' }).click()

  await expect.poll(getSent).toBe('')
})