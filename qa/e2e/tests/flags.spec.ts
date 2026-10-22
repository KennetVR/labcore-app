import { expect, test } from '@playwright/test'

const items = [
  {
    id: 1, examen: 11, examen_codigo: 'GLU', examen_nombre: 'Glucosa', paquete: null, paquete_nombre: '',
    cantidad: 1, medicion: 'unica', resultado: '150', bandera: 'H', bandera_manual: false,
    bandera_calculada: 'H', rango_estado: 'alto', unidad: 'mg/dL', ref_min: '70.0000', ref_max: '100.0000',
    ref_texto: '', validado_por: null, validado_at: null,
  },
  {
    id: 2, examen: 12, examen_codigo: 'HB', examen_nombre: 'Hemoglobina', paquete: null, paquete_nombre: '',
    cantidad: 1, medicion: 'unica', resultado: '14.2', bandera: '', bandera_manual: false,
    bandera_calculada: '', rango_estado: 'normal', unidad: 'g/dL', ref_min: '12.0000', ref_max: '16.0000',
    ref_texto: '', validado_por: null, validado_at: null,
  },
]
const baseOrder = {
  id: 5, numero: '202601010001', paciente_nombre: 'Perez, Ana', cliente_nombre: 'Particular',
  fecha: '2026-01-01', estado: 'registrada', total: '20.00', observacion: '', solicitado_por: '', items,
}

async function abrirOrden(page: import('@playwright/test').Page) {
  const guardado: { items: unknown[] } = { items: [] }
  await page.route(/\/api\/(auth|ordenes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    const method = route.request().method()
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 9, username: 'jefa', name: 'Jefa', role: 'encargada' }, csrf_token: 'test' } })
    }
    if (path === '/api/ordenes/5/resultados/' && method === 'POST') {
      guardado.items = (route.request().postDataJSON() as { items: unknown[] }).items
      return route.fulfill({ json: baseOrder })
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
  return guardado
}

test('muestra el rango de referencia y el estado calculado de cada examen', async ({ page }) => {
  await abrirOrden(page)

  await expect(page.getByRole('cell', { name: '70 - 100 mg/dL' })).toBeVisible()
  await expect(page.getByRole('cell', { name: '12 - 16 g/dL' })).toBeVisible()
  await expect(page.getByText('Alto')).toBeVisible()
  await expect(page.getByText('En rango')).toBeVisible()
})

test('envia la bandera sin marcar como manual si el laboratorio no la edita', async ({ page }) => {
  const guardado = await abrirOrden(page)

  await page.getByLabel('Resultado GLU').fill('160')
  await page.getByRole('button', { name: 'Guardar resultados' }).click()

  await expect.poll(() => guardado.items).toEqual([
    { id: 1, resultado: '160', bandera: 'H', bandera_manual: false },
    { id: 2, resultado: '14.2', bandera: '', bandera_manual: false },
  ])
})

test('marca la bandera como manual cuando el laboratorio la edita', async ({ page }) => {
  const guardado = await abrirOrden(page)

  await page.getByLabel('Bandera GLU').fill('H*')
  await expect(page.getByText('Alto · manual')).toBeVisible()
  await page.getByRole('button', { name: 'Guardar resultados' }).click()

  await expect.poll(() => guardado.items).toEqual([
    { id: 1, resultado: '150', bandera: 'H*', bandera_manual: true },
    { id: 2, resultado: '14.2', bandera: '', bandera_manual: false },
  ])
})

test('vaciar la bandera devuelve el control al calculo automatico', async ({ page }) => {
  const guardado = await abrirOrden(page)

  await page.getByLabel('Bandera GLU').fill('')
  await expect(page.getByText('Alto')).toBeVisible()
  await page.getByRole('button', { name: 'Guardar resultados' }).click()

  await expect.poll(() => guardado.items).toEqual([
    { id: 1, resultado: '150', bandera: '', bandera_manual: false },
    { id: 2, resultado: '14.2', bandera: '', bandera_manual: false },
  ])
})
