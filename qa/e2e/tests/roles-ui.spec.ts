import { expect, test } from '@playwright/test'

const exam = {
  id: 11, codigo: 'GLU', nombre: 'Glucosa', area: 'sangre', resultado_tipo: 'numerico',
  unidad: 'mg/dL', metodo: '', ref_min: '70.0000', ref_max: '110.0000', ref_texto: '',
  mide_pre_post: false, activo: true,
}

const order = {
  id: 1, numero: 'ORD-1', paciente_nombre: 'Demo, Ana', cliente_nombre: 'Demo',
  fecha: '2026-10-20', estado: 'validada', observacion: '', solicitado_por: '',
  total: '30.00', total_pagado: '0.00', saldo: '30.00', items: [], pagos: [], reporte: null,
}

async function mock(page: import('@playwright/test').Page, role: string) {
  await page.route(/\/api\/(auth|ordenes|examenes|paquetes|pacientes|clientes|tarifario-examenes|tarifario-paquetes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 9, username: 'qa', name: 'QA', role }, csrf_token: 'test' } })
    }
    if (path === '/api/ordenes/1/') return route.fulfill({ json: order })
    if (path === '/api/ordenes/1/envios/') return route.fulfill({ json: { results: [] } })
    const tables: Record<string, unknown[]> = {
      '/api/examenes/': [exam],
      '/api/paquetes/': [],
      '/api/pacientes/': [],
      '/api/clientes/': [],
      '/api/tarifario-examenes/': [],
      '/api/tarifario-paquetes/': [],
      '/api/ordenes/': [{ ...order, items: undefined }],
    }
    const results = tables[path] ?? []
    await route.fulfill({ json: { count: results.length, next: null, previous: null, results } })
  })
}

test('el encargado ve el catalogo en solo lectura', async ({ page }) => {
  await mock(page, 'encargada')
  await page.goto('/')
  await page.getByRole('button', { name: 'Catálogo', exact: true }).click()

  await expect(page.getByRole('cell', { name: 'GLU', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Nuevo examen' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Editar' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Eliminar' })).toHaveCount(0)
})

test('el encargado no ve la reapertura de una orden validada', async ({ page }) => {
  await mock(page, 'encargada')
  await page.goto('/')
  await page.getByRole('button', { name: 'Ver orden ORD-1', exact: true }).click()

  await expect(page.getByRole('heading', { name: 'ORD-1', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Reabrir para corregir' })).toHaveCount(0)
})

test('el administrador ve la reapertura de una orden validada', async ({ page }) => {
  await mock(page, 'admin')
  await page.goto('/')
  await page.getByRole('button', { name: 'Ver orden ORD-1', exact: true }).click()

  await expect(page.getByRole('button', { name: 'Reabrir para corregir' })).toBeVisible()
})
