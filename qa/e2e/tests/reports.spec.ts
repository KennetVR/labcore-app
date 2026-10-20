import { expect, test } from '@playwright/test'

test('generates a report and offers the PDF download', async ({ page }) => {
  let generated = false
  const items = [{ id: 1, examen: 11, examen_codigo: 'GLU', examen_nombre: 'Glucosa', paquete: null, paquete_nombre: '', cantidad: 1, medicion: 'unica', resultado: '95', bandera: '', validado_por: 9, validado_at: '2026-01-01T10:00:00Z' }]
  const order = {
    id: 5, numero: '202601010001', paciente_nombre: 'Perez, Ana', cliente_nombre: 'Particular',
    fecha: '2026-01-01', estado: 'validada', total: '20.00', observacion: '', solicitado_por: '', items,
    reporte: null as null | { id: number; numero: string; generado: string; pdf_url: string },
  }
  const reporte = { id: 3, numero: 'R202601010001', generado: '2026-01-01T11:00:00Z', pdf_url: '/api/reportes/3/pdf/' }

  await page.route(/\/api\/(auth|ordenes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    const method = route.request().method()
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 9, username: 'jefa', name: 'Jefa', role: 'encargada' }, csrf_token: 'test' } })
    }
    if (path === '/api/ordenes/5/reporte/' && method === 'POST') {
      generated = true
      return route.fulfill({ status: 201, json: reporte })
    }
    if (path === '/api/ordenes/5/') {
      return route.fulfill({ json: generated ? { ...order, estado: 'pdf', reporte } : order })
    }
    if (path === '/api/ordenes/') {
      return route.fulfill({ json: { count: 1, next: null, previous: null, results: [order] } })
    }
    return route.fulfill({ json: { count: 0, next: null, previous: null, results: [] } })
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Ver orden 202601010001' }).click()
  await page.getByRole('button', { name: 'Generar reporte' }).click()

  await expect.poll(() => generated).toBe(true)
  await expect(page.getByText('PDF generado')).toBeVisible()
  await expect(page.getByRole('link', { name: 'Descargar PDF R202601010001' }))
    .toHaveAttribute('href', '/api/reportes/3/pdf/')
})
