import { expect, test } from '@playwright/test'

test('list patients and register a new one', async ({ page }) => {
  let created = false
  const patient = {
    id: 7,
    dni: '12345678',
    apellidos: 'Flores',
    nombres: 'Ana',
    sexo: 'F',
    fecha_nacimiento: '1990-05-02',
    cliente: 2,
    observaciones: '',
    nombre_completo: 'Flores, Ana',
  }
  await page.route(/\/api\/(auth|pacientes|clientes)\//, async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 1, username: 'qa', name: 'QA', role: 'encargada' }, csrf_token: 'test' } })
    }
    if (path === '/api/pacientes/' && route.request().method() === 'POST') {
      expect(route.request().headers()['x-csrftoken']).toBe('test')
      expect(route.request().postDataJSON()).toMatchObject({
        dni: '12345678', apellidos: 'Flores', nombres: 'Ana', sexo: 'F', cliente: 2,
      })
      created = true
      return route.fulfill({ status: 201, json: patient })
    }
    const records: Record<string, unknown[]> = {
      '/api/pacientes/': created ? [patient] : [],
      '/api/clientes/': [{ id: 2, nombre: 'Demo Clinic' }],
    }
    const results = records[path] ?? []
    await route.fulfill({ json: { count: results.length, next: null, previous: null, results } })
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Pacientes', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Pacientes', exact: true })).toBeVisible()
  await expect(page.getByText('No hay pacientes para mostrar.')).toBeVisible()

  await page.getByRole('button', { name: 'Nuevo paciente' }).click()
  await page.getByLabel('Apellidos').fill('Flores')
  await page.getByLabel('Nombres', { exact: true }).fill('Ana')
  await page.getByLabel('DNI').fill('12345678')
  await page.getByLabel('Sexo').selectOption('F')
  await page.getByLabel('Fecha de nacimiento').fill('1990-05-02')
  await page.getByLabel('Cliente').selectOption('2')
  await page.getByRole('button', { name: 'Guardar paciente' }).click()

  await expect(page.getByText('Flores, Ana')).toBeVisible()
  await expect(page.getByText('12345678')).toBeVisible()
})
