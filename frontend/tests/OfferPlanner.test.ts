import { mountSuspended } from '@nuxt/test-utils/runtime'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import OfferPlanner from '~/components/OfferPlanner.vue'
import type { EvaluationResult } from '~/types/offers'
import { evaluateOffer } from '~/utils/offers'

vi.mock('~/utils/offers', async (importOriginal) => {
  const original = await importOriginal<typeof import('~/utils/offers')>()
  return { ...original, evaluateOffer: vi.fn() }
})

const successfulResult: EvaluationResult = {
  evaluation_id: 'eval-001',
  engine: 'pyqgis',
  source_crs: 'EPSG:4326',
  analysis_crs: 'EPSG:25830',
  recommended_segment_id: 'SEG-EAST',
  wms_preview_url: 'https://geo.example/wms?request=GetMap',
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
}

describe('OfferPlanner', () => {
  beforeEach(() => {
    vi.mocked(evaluateOffer).mockReset()
  })

  it('submits operator criteria and renders the recommendation', async () => {
    vi.mocked(evaluateOffer).mockResolvedValue(successfulResult)
    const wrapper = await mountSuspended(OfferPlanner, {
      props: { apiBase: 'http://api.test' },
    })
    await wrapper.get('[data-testid="maximum-distance"]').setValue('900')
    await wrapper.get('[data-testid="minimum-sites"]').setValue('3')
    await wrapper.get('form').trigger('submit')
    await vi.waitFor(() => expect(wrapper.find('[data-testid="evaluation-results"]').exists()).toBe(true))

    expect(evaluateOffer).toHaveBeenCalledWith(
      'http://api.test',
      expect.objectContaining({ maximum_distance_m: 900, minimum_demand_sites: 3 }),
    )
    expect(wrapper.get('[data-testid="recommended-segment"]').text()).toBe('SEG-EAST')
    expect(wrapper.text()).toContain('pyqgis')
  })

  it('shows a recoverable error state', async () => {
    vi.mocked(evaluateOffer).mockRejectedValue(new Error('WFS endpoint unavailable'))
    const wrapper = await mountSuspended(OfferPlanner, {
      props: { apiBase: 'http://api.test' },
    })
    await wrapper.get('form').trigger('submit')
    await vi.waitFor(() => expect(wrapper.find('[role="alert"]').exists()).toBe(true))
    expect(wrapper.text()).toContain('WFS endpoint unavailable')
  })
})
