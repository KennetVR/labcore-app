import { expect, test } from '@playwright/test'

const baseItems = [
  { id: 1, examen: 11, examen_codigo: 'GLU', examen_nombre: 'Glucosa', paquete: null, paquete_nombre: '', cantidad: 1, medicion: 'unica', resultado: '', bandera: '', validado_por: null, validado_at: null },
  { id: 2, examen: 12, examen_codigo: 'HEM', examen_nombre: 'Hemograma', paquete: null, paquete_nombre: '', cantidad: 1, medicion: 'unica', resultado: '', bandera: '', validado_por: null, validado_at: null },
]
const baseOrder = {
  id: 5, numero: '202601010001', paciente_nombre: 'Perez, Ana', cliente_nombre: 'Particular',
  fecha: '2026-01-01', estado: 'registrada', total: '20.00', observacion: '', solicitado_por: '',
  items: baseItems,
}

test('capture and validate order results', async ({ page }) => {
  let saved: unknown = null
  let validated = false
  await page.route(/\/api\/(auth|ordenes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    const method = route.request().method()
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 9, username: 'jefa', name: 'Jefa', role: 'encargada' }, csrf_token: 'test' } })
    }
    if (path === '/api/ordenes/5/resultados/' && method === 'POST') {
      saved = route.request().postDataJSON()
      const items = baseItems.map(item => ({
        ...item,
        resultado: item.id === 1 ? '95' : '14.2',
        bandera: item.id === 2 ? 'H' : '',
      }))
      return route.fulfill({ json: { ...baseOrder, estado: 'en_proceso', items } })
    }
    if (path === '/api/ordenes/5/validar/' && method === 'POST') {
      validated = true
      const items = baseItems.map(item => ({ ...item, resultado: '1', validado_por: 9, validado_at: '2026-01-01T10:00:00Z' }))
      return route.fulfill({ json: { ...baseOrder, estado: 'validada', items } })
    }
    if (path === '/api/ordenes/5/') return route.fulfill({ json: baseOrder })
    if (path === '/api/ordenes/') {
      return route.fulfill({ json: { count: 1, next: null, previous: null, results: [baseOrder] } })
    }
    return route.fulfill({ json: { count: 0, next: null, previous: null, results: [] } })
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Ver orden 202601010001' }).click()
  await expect(page.getByRole('heading', { name: '202601010001' })).toBeVisible()

  await page.getByLabel('Resultado GLU').fill('95')
  await page.getByLabel('Resultado HEM').fill('14.2')
  await page.getByLabel('Bandera HEM').fill('H')
  await page.getByRole('button', { name: 'Guardar resultados' }).click()

  await expect.poll(() => saved).toEqual({
    items: [
      { id: 1, resultado: '95', bandera: '' },
      { id: 2, resultado: '14.2', bandera: 'H' },
    ],
  })
  await expect(page.getByText('En proceso')).toBeVisible()

  await page.getByRole('button', { name: 'Validar resultados' }).click()
  await expect.poll(() => validated).toBe(true)
  await expect(page.getByText('Validada', { exact: true })).toBeVisible()
})
