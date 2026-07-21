import type {
  CandidateView,
  EvaluationRequest,
  EvaluationResult,
} from '~/types/offers'

export type JsonRequester = <T>(
  url: string,
  options: { method: 'POST'; body: EvaluationRequest },
) => Promise<T>

export async function evaluateOffer(
  apiBase: string,
  request: EvaluationRequest,
  requester: JsonRequester = $fetch,
): Promise<EvaluationResult> {
  const normalizedBase = apiBase.replace(/\/$/, '')
  return requester<EvaluationResult>(`${normalizedBase}/api/v1/offers/evaluate`, {
    method: 'POST',
    body: request,
  })
}
export function candidateViews(result: EvaluationResult): CandidateView[] {
  return result.candidates.map((candidate) => ({
    ...candidate,
    lengthLabel: `${(candidate.length_m / 1000).toFixed(2)} km`,
    coverageLabel: `${candidate.coverage_percent.toFixed(1)}%`,
    recommendation: candidate.segment_id === result.recommended_segment_id,
  }))
}
