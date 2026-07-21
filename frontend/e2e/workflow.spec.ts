import { expect, test } from '@playwright/test'

test('operator evaluates corridors and sees a recommended segment', async ({ page }) => {
  const runtimeResponse = await page.request.get('/api/runtime')
  expect(runtimeResponse.ok()).toBe(true)
  await expect(runtimeResponse.json()).resolves.toEqual({
    service: 'network-offer-geodata-client',
    runtime: 'node',
    status: 'ok',
  })

  await page.route('**/api/v1/offers/evaluate', async (route) => {
    const request = route.request().postDataJSON()
    expect(request.maximum_distance_m).toBe(900)
    await route.fulfill({
      contentType: 'application/json',
      body: JSON.stringify({
        evaluation_id: 'browser-eval-001',
        engine: 'pyqgis',
        source_crs: 'EPSG:4326',
        analysis_crs: 'EPSG:25830',
        recommended_segment_id: 'SEG-EAST',
        wms_preview_url: 'http://127.0.0.1:8000/fixtures/wms?request=GetMap',
        candidates: [
          {
            segment_id: 'SEG-EAST',
            name: 'Eastern service corridor',
            length_m: 2888.4,
            demand_sites: 2,
            coverage_percent: 33.33,
            available_capacity_gbps: 100,
            eligible: true,
          },
        ],
      }),
    })
  })

  await page.goto('/')
  await expect(page.getByRole('heading', { name: /Network offer planning/ })).toBeVisible()
  await page.getByTestId('maximum-distance').fill('900')
  await page.getByRole('button', { name: 'Run offer evaluation' }).click()
  await expect(page.getByTestId('recommended-segment')).toHaveText('SEG-EAST')
  await expect(page.getByRole('link', { name: 'Open WMS preview' })).toBeVisible()
})
