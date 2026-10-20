import { expect, test } from '@playwright/test'

test('register a package with its exams', async ({ page }) => {
  let created = false
  const pkg = {
    id: 7, nombre: 'Control Anual', frecuencia: 'semestral', activo: true,
    examenes: [{ orden: 0, examen: 11 }, { orden: 1, examen: 12 }],
  }
  await page.route(/\/api\/(auth|examenes|paquetes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 1, username: 'qa', name: 'QA', role: 'auxiliar' }, csrf_token: 'test' } })
    }
    if (path === '/api/paquetes/' && route.request().method() === 'POST') {
      expect(route.request().postDataJSON()).toEqual({
        nombre: 'Control Anual',
        frecuencia: 'semestral',
        activo: true,
        examenes: [{ examen: 11, orden: 0 }, { examen: 12, orden: 1 }],
      })
      created = true
      return route.fulfill({ status: 201, json: pkg })
    }
    const records: Record<string, unknown[]> = {
      '/api/examenes/': [
        { id: 11, codigo: 'GLU', nombre: 'Glucosa' },
        { id: 12, codigo: 'HEM', nombre: 'Hemograma' },
      ],
      '/api/paquetes/': created ? [pkg] : [],
    }
    const results = records[path] ?? []
    await route.fulfill({ json: { count: results.length, next: null, previous: null, results } })
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Catálogo', exact: true }).click()
  await page.getByRole('tab', { name: 'Paquetes' }).click()
  await expect(page.getByText('No hay paquetes para mostrar.')).toBeVisible()

  await page.getByRole('button', { name: 'Nuevo paquete' }).click()
  await page.getByLabel('Nombre', { exact: true }).fill('Control Anual')
  await page.getByLabel('Frecuencia').selectOption('semestral')
  await page.getByLabel('GLU - Glucosa').check()
  await page.getByLabel('HEM - Hemograma').check()
  await page.getByRole('button', { name: 'Guardar paquete' }).click()

  await expect(page.getByText('Control Anual')).toBeVisible()
  await expect(page.getByText('2 exámenes')).toBeVisible()
})
