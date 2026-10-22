import { expect, test } from '@playwright/test'

test('list exams and packages, and register an exam', async ({ page }) => {
  let created = false
  const exam = {
    id: 11, codigo: 'GLU', nombre: 'Glucosa', area: 'sangre', resultado_tipo: 'numerico',
    unidad: 'mg/dL', metodo: 'Enzimático', ref_min: '70.0000', ref_max: '110.0000', ref_texto: '',
    mide_pre_post: false, activo: true,
  }
  await page.route(/\/api\/(auth|examenes|paquetes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 1, username: 'qa', name: 'QA', role: 'admin' }, csrf_token: 'test' } })
    }
    if (path === '/api/examenes/' && route.request().method() === 'POST') {
      expect(route.request().postDataJSON()).toMatchObject({
        codigo: 'GLU', nombre: 'Glucosa', area: 'sangre', resultado_tipo: 'numerico',
        unidad: 'mg/dL', ref_min: '70', ref_max: '110', mide_pre_post: false, activo: true,
      })
      created = true
      return route.fulfill({ status: 201, json: exam })
    }
    const records: Record<string, unknown[]> = {
      '/api/examenes/': created ? [exam] : [],
      '/api/paquetes/': [{ id: 4, nombre: 'Control Mensual', frecuencia: 'mensual', activo: true, examenes: [{ orden: 1, examen: 9 }, { orden: 2, examen: 10 }] }],
    }
    const results = records[path] ?? []
    await route.fulfill({ json: { count: results.length, next: null, previous: null, results } })
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Catálogo', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Catálogo', exact: true })).toBeVisible()
  await expect(page.getByText('No hay exámenes para mostrar.')).toBeVisible()

  await page.getByRole('button', { name: 'Nuevo examen' }).click()
  await page.getByLabel('Código').fill('GLU')
  await page.getByLabel('Nombre', { exact: true }).fill('Glucosa')
  await page.getByLabel('Unidad').fill('mg/dL')
  await page.getByLabel('Mínimo').fill('70')
  await page.getByLabel('Máximo').fill('110')
  await page.getByRole('button', { name: 'Guardar examen' }).click()

  await expect(page.getByText('GLU', { exact: true })).toBeVisible()
  await expect(page.getByText('Glucosa')).toBeVisible()

  await page.getByRole('tab', { name: 'Paquetes' }).click()
  await expect(page.getByText('Control Mensual')).toBeVisible()
  await expect(page.getByText('2 exámenes')).toBeVisible()
})
