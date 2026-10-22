import { expect, test } from '@playwright/test'
import type { Page } from '@playwright/test'

type Reply = { status?: number; json?: unknown }

async function mock(page: Page, resources: string[], handler: (path: string, method: string, body: unknown) => Reply | undefined) {
  await page.route(new RegExp(`/api/(auth|${resources.join('|')})/`), async route => {
    const path = new URL(route.request().url()).pathname
    if (path === '/api/auth/session/') {
      return route.fulfill({ json: { user: { id: 1, username: 'qa', name: 'QA', role: 'admin' }, csrf_token: 'test' } })
    }
    const reply = handler(path, route.request().method(), route.request().postDataJSON())
    if (reply) return route.fulfill({ status: reply.status ?? 200, json: reply.json ?? {} })
    return route.fulfill({ json: { count: 0, next: null, previous: null, results: [] } })
  })
}

const listed = (results: unknown[]) => ({ json: { count: results.length, next: null, previous: null, results } })

test('edits and deletes a patient', async ({ page }) => {
  const patient = { id: 1, dni: '123', apellidos: 'Perez', nombres: 'Ana', sexo: 'F', fecha_nacimiento: null, cliente: null, observaciones: '', nombre_completo: 'Perez, Ana' }
  let patched: unknown = null
  let deleted = false
  await mock(page, ['pacientes', 'clientes'], (path, method, body) => {
    if (path === '/api/pacientes/1/' && method === 'PATCH') { patched = body; return { json: { ...patient, ...(body as object) } } }
    if (path === '/api/pacientes/1/' && method === 'DELETE') { deleted = true; return { status: 204 } }
    if (path === '/api/pacientes/') return listed([patient])
    return undefined
  })
  page.on('dialog', dialog => dialog.accept())

  await page.goto('/')
  await page.getByRole('button', { name: 'Pacientes', exact: true }).click()
  await page.getByRole('button', { name: 'Editar' }).click()
  await page.getByLabel('Apellidos').fill('Perez Soto')
  await page.getByRole('button', { name: 'Guardar cambios' }).click()
  await expect.poll(() => patched).toMatchObject({ apellidos: 'Perez Soto' })

  await page.getByRole('button', { name: 'Eliminar' }).click()
  await expect.poll(() => deleted).toBe(true)
})

test('edits a client', async ({ page }) => {
  const client = { id: 2, nombre: 'Clinica Sur', tipo: 'clinica', zona: null, contacto: '', activo: true }
  let patched: unknown = null
  await mock(page, ['clientes', 'zonas'], (path, method, body) => {
    if (path === '/api/clientes/2/' && method === 'PATCH') { patched = body; return { json: { ...client, ...(body as object) } } }
    if (path === '/api/clientes/') return listed([client])
    return undefined
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Clientes', exact: true }).click()
  await page.getByRole('button', { name: 'Editar' }).click()
  await page.getByLabel('Nombre', { exact: true }).fill('Clinica Norte')
  await page.getByRole('button', { name: 'Guardar cambios' }).click()
  await expect.poll(() => patched).toMatchObject({ nombre: 'Clinica Norte' })
})

test('edits an exam', async ({ page }) => {
  const exam = { id: 11, codigo: 'GLU', nombre: 'Glucosa', area: 'sangre', resultado_tipo: 'numerico', unidad: 'mg/dL', metodo: '', ref_min: '70.0000', ref_max: '110.0000', ref_texto: '', mide_pre_post: false, activo: true }
  let patched: unknown = null
  await mock(page, ['examenes', 'paquetes'], (path, method, body) => {
    if (path === '/api/examenes/11/' && method === 'PATCH') { patched = body; return { json: { ...exam, ...(body as object) } } }
    if (path === '/api/examenes/') return listed([exam])
    return undefined
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Catálogo', exact: true }).click()
  await page.getByRole('button', { name: 'Editar' }).click()
  await page.getByLabel('Unidad').fill('g/dL')
  await page.getByRole('button', { name: 'Guardar cambios' }).click()
  await expect.poll(() => patched).toMatchObject({ unidad: 'g/dL' })
})

test('edits a package composition', async ({ page }) => {
  const pkg = { id: 4, nombre: 'Control', frecuencia: 'mensual', activo: true, examenes: [{ orden: 0, examen: 11 }] }
  let patched: unknown = null
  await mock(page, ['examenes', 'paquetes'], (path, method, body) => {
    if (path === '/api/paquetes/4/' && method === 'PATCH') { patched = body; return { json: pkg } }
    if (path === '/api/paquetes/') return listed([pkg])
    if (path === '/api/examenes/') return listed([
      { id: 11, codigo: 'GLU', nombre: 'Glucosa' },
      { id: 12, codigo: 'HEM', nombre: 'Hemograma' },
    ])
    return undefined
  })

  await page.goto('/')
  await page.getByRole('button', { name: 'Catálogo', exact: true }).click()
  await page.getByRole('tab', { name: 'Paquetes' }).click()
  await page.getByRole('button', { name: 'Editar' }).click()
  await page.getByLabel('HEM - Hemograma').check()
  await page.getByRole('button', { name: 'Guardar cambios' }).click()
  await expect.poll(() => patched).toMatchObject({
    examenes: [{ examen: 11, orden: 0 }, { examen: 12, orden: 1 }],
  })
})

test('deletes a tariff', async ({ page }) => {
  const tariff = { id: 8, examen: 11, examen_codigo: 'HB', examen_nombre: 'Hemoglobina', precio: '15.00', zona: null, zona_nombre: null, cliente: null, cliente_nombre: null, vigencia_desde: null, activo: true }
  let deleted = false
  await mock(page, ['tarifario-examenes', 'tarifario-paquetes', 'examenes', 'paquetes', 'zonas', 'clientes'], (path, method) => {
    if (path === '/api/tarifario-examenes/8/' && method === 'DELETE') { deleted = true; return { status: 204 } }
    if (path === '/api/tarifario-examenes/') return listed([tariff])
    return undefined
  })
  page.on('dialog', dialog => dialog.accept())

  await page.goto('/')
  await page.getByRole('button', { name: 'Tarifarios', exact: true }).click()
  await page.getByRole('button', { name: 'Eliminar' }).click()
  await expect.poll(() => deleted).toBe(true)
})
