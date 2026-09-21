import { expect, test } from '@playwright/test'

test('la pantalla inicial muestra el titulo del sistema', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByRole('heading', { name: 'LabCore' })).toBeVisible()
  await expect(page.getByText('Sistema de gestión para laboratorio clínico')).toBeVisible()
})