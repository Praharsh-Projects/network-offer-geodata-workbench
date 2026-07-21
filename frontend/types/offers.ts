export interface EvaluationRequest {
  bbox: [number, number, number, number]
  maximum_distance_m: number
  minimum_demand_sites: number
}
export interface SegmentEvaluation {
  segment_id: string
  name: string
  length_m: number
  demand_sites: number
  coverage_percent: number
  available_capacity_gbps: number
  eligible: boolean
}

export interface EvaluationResult {
  evaluation_id: string
  engine: string
  source_crs: string
  analysis_crs: string
  recommended_segment_id: string | null
  wms_preview_url: string
  candidates: SegmentEvaluation[]
}

export interface CandidateView extends SegmentEvaluation {
  lengthLabel: string
  coverageLabel: string
  recommendation: boolean
}
