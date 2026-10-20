import { expect, test } from '@playwright/test'

const items = [{ id: 1, examen: 11, examen_codigo: 'GLU', examen_nombre: 'Glucosa', paquete: null, paquete_nombre: '', cantidad: 1, medicion: 'unica', resultado: '95', bandera: '', validado_por: 9, validado_at: '2026-01-01T10:00:00Z' }]
const reporte = { id: 3, numero: 'R202601010001', generado: '2026-01-01T11:00:00Z', pdf_url: '/api/reportes/3/pdf/', enviado_a: '', entregado_at: null as string | null, entregado_por: null as string | null }
const baseOrder = {
  id: 5, numero: '202601010001', paciente_nombre: 'Perez, Ana', cliente_nombre: 'Particular',
  fecha: '2026-01-01', estado: 'pdf', total: '20.00', observacion: '', solicitado_por: '', items, reporte,
}

async function openOrder(page: import('@playwright/test').Page, entregada: (enviadoA: string) => unknown) {
  await page.route(/\/api\/(auth|ordenes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    const method = route.request().method()
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 9, username: 'jefa', name: 'Jefa', role: 'reportes' }, csrf_token: 'test' } })
    }
    if (path === '/api/ordenes/5/entrega/' && method === 'POST') {
      const body = route.request().postDataJSON() as { enviado_a: string }
      return route.fulfill({ json: entregada(body.enviado_a) })
    }
    if (path === '/api/ordenes/5/') return route.fulfill({ json: baseOrder })
    if (path === '/api/ordenes/') {
      return route.fulfill({ json: { count: 1, next: null, previous: null, results: [baseOrder] } })
    }
    return route.fulfill({ json: { count: 0, next: null, previous: null, results: [] } })
  })
  await page.goto('/')
  await page.getByRole('button', { name: 'Ver orden 202601010001' }).click()
}

test('sends the report by email and registers delivery', async ({ page }) => {
  let sent: unknown = null
  await openOrder(page, enviadoA => {
    sent = enviadoA
    return {
      ...baseOrder, estado: 'entregada',
      reporte: { ...reporte, enviado_a: enviadoA, entregado_at: '2026-01-01T12:00:00Z', entregado_por: 'Jefa' },
    }
  })

  await page.getByLabel('Correo de entrega (opcional)').fill('ana@example.com')
  await page.getByRole('button', { name: 'Enviar y entregar' }).click()

  await expect.poll(() => sent).toBe('ana@example.com')
  await expect(page.getByText('Entregada', { exact: true })).toBeVisible()
  await expect(page.getByText(/por correo a ana@example\.com/)).toBeVisible()
})

test('registers an in-hand delivery without email', async ({ page }) => {
  let sent: unknown = null
  await openOrder(page, enviadoA => {
    sent = enviadoA
    return {
      ...baseOrder, estado: 'entregada',
      reporte: { ...reporte, enviado_a: '', entregado_at: '2026-01-01T12:00:00Z', entregado_por: 'Jefa' },
    }
  })

  await page.getByRole('button', { name: 'Registrar entrega' }).click()

  await expect.poll(() => sent).toBe('')
  await expect(page.getByText(/Entregada.*en mano/)).toBeVisible()
})
