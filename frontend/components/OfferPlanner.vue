<script setup lang="ts">
import type { EvaluationRequest, EvaluationResult } from '~/types/offers'
import { candidateViews, evaluateOffer } from '~/utils/offers'

const props = withDefaults(defineProps<{ apiBase?: string }>(), {
  apiBase: '',
})

const runtimeConfig = useRuntimeConfig()
const resolvedApiBase = computed(
  () => props.apiBase || String(runtimeConfig.public.apiBase),
)

const maximumDistance = ref(750)
const minimumSites = ref(2)
const result = ref<EvaluationResult | null>(null)
const status = ref<'idle' | 'loading' | 'success' | 'error'>('idle')
const errorMessage = ref('')

const candidates = computed(() => (result.value ? candidateViews(result.value) : []))
const recommended = computed(() =>
  candidates.value.find((candidate) => candidate.recommendation),
)

async function runEvaluation() {
  status.value = 'loading'
  errorMessage.value = ''
  const request: EvaluationRequest = {
    bbox: [-3.66, 37.14, -3.52, 37.23],
    maximum_distance_m: maximumDistance.value,
    minimum_demand_sites: minimumSites.value,
  }
  try {
    result.value = await evaluateOffer(resolvedApiBase.value, request)
    status.value = 'success'
  } catch (error) {
    status.value = 'error'
    errorMessage.value = error instanceof Error ? error.message : 'Evaluation request failed.'
  }
}
</script>

<template>
  <section class="workspace" aria-labelledby="workspace-title">
    <aside class="control-panel">
      <div>
        <p class="eyebrow">Evaluation controls</p>
        <h2 id="workspace-title">Offer criteria</h2>
        <p class="panel-copy">
          Adjust the maximum corridor distance and the minimum number of demand sites required for an
          eligible offer.
        </p>
      </div>

      <form @submit.prevent="runEvaluation">
        <label for="distance">Maximum site distance</label>
        <div class="field-with-unit">
          <input
            id="distance"
            v-model.number="maximumDistance"
            data-testid="maximum-distance"
            type="number"
            min="25"
            max="5000"
            step="25"
            required
          >
          <span>metres</span>
        </div>

        <label for="minimum-sites">Minimum demand sites</label>
        <input
          id="minimum-sites"
          v-model.number="minimumSites"
          data-testid="minimum-sites"
          type="number"
          min="1"
          max="100"
          required
        >

        <button type="submit" :disabled="status === 'loading'">
          <span v-if="status === 'loading'">Evaluating corridors...</span>
          <span v-else>Run offer evaluation</span>
        </button>
      </form>

      <div class="contract-note">
        <strong>Request boundary</strong>
        <span>Granada synthetic planning extent</span>
        <code>-3.66, 37.14, -3.52, 37.23</code>
      </div>
    </aside>

    <div class="result-panel" aria-live="polite">
      <div v-if="status === 'idle'" class="empty-state">
        <div class="empty-state__network" aria-hidden="true">
          <span /><span /><span /><span />
        </div>
        <p class="eyebrow">Ready for evaluation</p>
        <h2>Compare candidate corridors</h2>
        <p>Run the workflow to retrieve WFS features and rank the synthetic network segments.</p>
      </div>

      <div v-else-if="status === 'loading'" class="empty-state">
        <div class="loader" aria-hidden="true" />
        <h2>Processing geodata</h2>
        <p>Fetching feature collections and applying projected distance checks.</p>
      </div>

      <div v-else-if="status === 'error'" class="error-state" role="alert">
        <p class="eyebrow">Request failed</p>
        <h2>The evaluation could not be completed.</h2>
        <p>{{ errorMessage }}</p>
      </div>

      <div v-else-if="result" class="results" data-testid="evaluation-results">
        <div class="results__heading">
          <div>
            <p class="eyebrow">Evaluation complete</p>
            <h2>{{ recommended ? recommended.name : 'No eligible corridor' }}</h2>
            <p v-if="recommended" class="panel-copy">
              Recommended from {{ candidates.length }} candidates using {{ result.engine }} geometry processing.
            </p>
          </div>
          <a :href="result.wms_preview_url" target="_blank" rel="noreferrer">
            Open WMS preview
          </a>
        </div>

        <div class="metric-grid">
          <div>
            <span>Recommended segment</span>
            <strong data-testid="recommended-segment">{{ result.recommended_segment_id || 'None' }}</strong>
          </div>
          <div>
            <span>Geometry engine</span>
            <strong>{{ result.engine }}</strong>
          </div>
          <div>
            <span>Analysis CRS</span>
            <strong>{{ result.analysis_crs }}</strong>
          </div>
        </div>

        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Candidate</th>
                <th>Demand</th>
                <th>Coverage</th>
                <th>Capacity</th>
                <th>Length</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="candidate in candidates" :key="candidate.segment_id">
                <td>
                  <strong>{{ candidate.name }}</strong>
                  <span>{{ candidate.segment_id }}</span>
                </td>
                <td>{{ candidate.demand_sites }} sites</td>
                <td>{{ candidate.coverageLabel }}</td>
                <td>{{ candidate.available_capacity_gbps }} Gbps</td>
                <td>{{ candidate.lengthLabel }}</td>
                <td>
                  <span
                    class="status-pill"
                    :class="candidate.eligible ? 'status-pill--eligible' : 'status-pill--review'"
                  >
                    {{ candidate.recommendation ? 'Recommended' : candidate.eligible ? 'Eligible' : 'Review' }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <p class="evaluation-id">Evaluation ID: {{ result.evaluation_id }}</p>
      </div>
    </div>
  </section>
</template>
