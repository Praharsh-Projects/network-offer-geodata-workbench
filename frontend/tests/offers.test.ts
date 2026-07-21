import { describe, expect, it, vi } from 'vitest'

import type { EvaluationResult } from '~/types/offers'
import { candidateViews, evaluateOffer } from '~/utils/offers'

const result: EvaluationResult = {
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
      coverage_percent: 33.333,
      available_capacity_gbps: 100,
      eligible: true,
    },
  ],
}

describe('offer API and view transforms', () => {
  it('posts a typed evaluation request to a normalized API base URL', async () => {
    const requester = vi.fn().mockResolvedValue(result)
    const request = {
      bbox: [-3.66, 37.14, -3.52, 37.23] as [number, number, number, number],
      maximum_distance_m: 750,
      minimum_demand_sites: 2,
    }
    const response = await evaluateOffer('http://localhost:8000/', request, requester)
    expect(response).toEqual(result)
    expect(requester).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/offers/evaluate',
      { method: 'POST', body: request },
    )
  })

  it('formats candidate measurements and marks the recommendation', () => {
    expect(candidateViews(result)).toEqual([
      expect.objectContaining({
        segment_id: 'SEG-EAST',
        lengthLabel: '2.89 km',
        coverageLabel: '33.3%',
        recommendation: true,
      }),
    ])
  })

  it('does not mark a candidate when no recommendation exists', () => {
    const withoutRecommendation = { ...result, recommended_segment_id: null }
    expect(candidateViews(withoutRecommendation)[0]?.recommendation).toBe(false)
  })
})
