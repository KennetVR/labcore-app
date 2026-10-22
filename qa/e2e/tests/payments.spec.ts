import { expect, test } from '@playwright/test'

const order = {
  id: 5, numero: '202601010001', paciente_nombre: 'Perez, Ana', cliente_nombre: 'Clínica San Juan',
  fecha: '2026-01-01', estado: 'entregada', total: '200.00', observacion: '', solicitado_por: '',
  total_pagado: '50.00', saldo: '150.00',
  items: [],
  reporte: null,
  pagos: [
    {
      id: 1, orden: 5, orden_numero: '202601010001', orden_total: '200.00', orden_cliente: 'Clínica San Juan',
      monto: '50.00', forma_pago: 'contado' as const, observacion: 'Abono', registrado_por: 9,
      registrado_por_nombre: 'Jefa', fecha: '2026-01-02T10:00:00Z', anulado: false, anulado_por: null,
      anulado_por_nombre: '', anulado_at: null, motivo_anulacion: '', total_pagado: '50.00', saldo: '150.00',
    },
  ],
}

const statement = [
  { cliente_id: 3, cliente: 'Clínica San Juan', facturado: '200.00', pagado: '50.00', saldo: '150.00' },
]

async function mockear(page: import('@playwright/test').Page, rol = 'reportes') {
  const guardados: unknown[] = []
  const anulados: { id: number; motivo: string }[] = []
  await page.route(/\/api\/(auth|ordenes|pagos|clientes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    const method = route.request().method()
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 9, username: 'jefa', name: 'Jefa', role: rol }, csrf_token: 'test' } })
    }
    if (path === '/api/pagos/estado-cuenta/') {
      return route.fulfill({ json: statement })
    }
    if (path === '/api/pagos/' && method === 'POST') {
      guardados.push(route.request().postDataJSON())
      return route.fulfill({ json: { ...order.pagos[0], id: 2 } })
    }
    if (path.startsWith('/api/pagos/') && path.endsWith('/anular/') && method === 'POST') {
      const id = Number(path.split('/')[3])
      anulados.push({ id, motivo: (route.request().postDataJSON() as { motivo: string }).motivo })
      return route.fulfill({ json: { ...order.pagos[0], id, anulado: true } })
    }
    if (path === '/api/pagos/') {
      return route.fulfill({ json: { count: order.pagos.length, next: null, previous: null, results: order.pagos } })
    }
    if (path === '/api/clientes/') {
      return route.fulfill({ json: { count: 1, next: null, previous: null, results: [{ id: 3, nombre: 'Clínica San Juan', tipo: 'clinica', zona: null, contacto: '', activo: true }] } })
    }
    if (path === '/api/ordenes/5/') return route.fulfill({ json: order })
    if (path === '/api/ordenes/') {
      return route.fulfill({ json: { count: 1, next: null, previous: null, results: [order] } })
    }
    return route.fulfill({ json: { count: 0, next: null, previous: null, results: [] } })
  })
  return { guardados, anulados }
}

test('la pantalla de pagos muestra el estado de cuenta y el listado', async ({ page }) => {
  await mockear(page)
  await page.goto('/')
  await page.getByRole('button', { name: 'Órdenes' }).waitFor()
  await page.getByRole('button', { name: 'Pagos' }).click()

  await expect(page.getByRole('heading', { name: 'Pagos', exact: true })).toBeVisible()
  await expect(page.getByText('Estado de cuenta')).toBeVisible()
  const cuenta = page.locator('section:has(h2:text("Estado de cuenta"))')
  await expect(cuenta.getByRole('cell', { name: 'Clínica San Juan' })).toBeVisible()
  await expect(cuenta.getByRole('cell', { name: 'S/ 200.00' })).toBeVisible()
  await expect(cuenta.getByRole('cell', { name: 'S/ 50.00' })).toBeVisible()
  await expect(cuenta.getByRole('cell', { name: 'S/ 150.00' })).toBeVisible()
  const listado = page.locator('section:has(h2:text("Pagos registrados"))')
  await expect(listado.getByRole('cell', { name: 'S/ 50.00' })).toBeVisible()
  await expect(listado.getByText('Vigente', { exact: true })).toBeVisible()
})

test('registra un pago desde la pantalla de pagos', async ({ page }) => {
  const { guardados } = await mockear(page)
  await page.goto('/')
  await page.getByRole('button', { name: 'Órdenes' }).waitFor()
  await page.getByRole('button', { name: 'Pagos' }).click()

  const form = page.locator('form')
  await form.getByLabel('Orden').selectOption('5')
  await form.getByLabel('Monto').fill('75')
  await form.getByLabel('Forma de pago').selectOption('factura')
  await form.getByLabel('Observación').fill('Abono de caja')
  await page.getByRole('button', { name: 'Registrar pago' }).click()

  await expect.poll(() => guardados).toEqual([
    { orden: 5, monto: '75', forma_pago: 'factura', observacion: 'Abono de caja' },
  ])
})

test('anula un pago indicando el motivo', async ({ page }) => {
  const { anulados } = await mockear(page)
  await page.goto('/')
  await page.getByRole('button', { name: 'Órdenes' }).waitFor()
  await page.getByRole('button', { name: 'Pagos' }).click()

  page.once('dialog', dialog => dialog.accept('Monto mal tipeado'))
  await page.getByRole('button', { name: 'Anular' }).click()

  await expect.poll(() => anulados).toEqual([{ id: 1, motivo: 'Monto mal tipeado' }])
})

test('el rol auxiliar no ve el formulario ni el boton de anular', async ({ page }) => {
  await mockear(page, 'auxiliar')
  await page.goto('/')
  await page.getByRole('button', { name: 'Órdenes' }).waitFor()
  await page.getByRole('button', { name: 'Pagos' }).click()

  await expect(page.getByRole('button', { name: 'Registrar pago' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Anular' })).toHaveCount(0)
  await expect(page.getByText('Estado de cuenta')).toBeVisible()
})

test('el detalle de la orden muestra el saldo y permite registrar el pago', async ({ page }) => {
  const { guardados } = await mockear(page)
  await page.goto('/')
  await page.getByRole('button', { name: 'Órdenes' }).waitFor()
  await page.getByRole('button', { name: 'Ver orden 202601010001' }).click()
  await expect(page.getByRole('heading', { name: '202601010001' })).toBeVisible()

  await expect(page.getByText('Saldo')).toBeVisible()
  await expect(page.getByRole('term').filter({ hasText: 'Saldo' })).toBeVisible()
  await expect(page.getByText('S/ 150.00')).toBeVisible()

  await page.getByLabel('Monto del pago').fill('150')
  await page.getByRole('button', { name: 'Registrar pago' }).click()

  await expect.poll(() => guardados).toEqual([
    { orden: 5, monto: '150', forma_pago: 'contado', observacion: '' },
  ])
})
