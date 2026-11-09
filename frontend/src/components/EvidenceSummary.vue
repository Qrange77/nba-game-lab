<script setup lang="ts">
import type { EvidenceResult } from '../types'
defineProps<{ result: EvidenceResult }>()
function number(value: number | null) { return value != null && Number.isFinite(value) ? value.toLocaleString('en-US', { maximumFractionDigits: 2 }) : 'Unavailable' }
function safeLink(value: string) {
  try { const url = new URL(value); return url.protocol === 'https:' && (url.hostname === 'nba.com' || url.hostname.endsWith('.nba.com')) ? url.href : undefined } catch { return undefined }
}
</script>
<template>
  <section class="evidence-section" aria-label="Sources and evidence checks">
    <div class="evidence-heading"><strong>Evidence & sources</strong><span>{{ result.verification.status === 'checked' ? `${result.verification.checked_claims} numeric claims checked` : 'Answer checks incomplete' }}</span></div>
    <section v-for="comparison in result.comparisons" :key="comparison.evidence_id || comparison.left_player" class="honors-panel stats-comparison">
      <strong>{{ comparison.kind === 'key_teammates' ? 'Selected teammate comparison' : 'Player comparison' }}</strong>
      <p class="honors-scope">{{ comparison.left_player }}: {{ comparison.left_scope }}<br />{{ comparison.right_player }}: {{ comparison.right_scope }}</p>
      <div class="comparison-scroll"><table class="honors-table"><thead><tr><th scope="col">Metric</th><th scope="col">{{ comparison.left_player }}</th><th scope="col">{{ comparison.right_player }}</th></tr></thead>
        <tbody><tr v-for="row in comparison.rows" :key="row.metric"><th scope="row">{{ row.label }}<small class="comparison-unit">{{ row.unit }}<template v-if="!row.comparable"> · Incomplete comparison</template></small></th><td>{{ number(row.left_value) }}</td><td>{{ number(row.right_value) }}</td></tr></tbody>
      </table></div>
      <p v-for="note in comparison.limitations" :key="note" class="picker-note">{{ note }}</p>
    </section>
    <div class="evidence-grid"><article v-for="(card, i) in result.cards" :key="`${card.evidence_id}-${i}`" class="evidence-card">
      <h3>{{ card.label || card.title }} <small>{{ card.unit }}</small></h3>
      <div class="evidence-value"><span>{{ card.player }}</span><strong>{{ number(card.value) }}</strong></div><p>{{ card.scope }}<template v-if="card.games != null"> · {{ card.games }} games</template></p>
      <template v-if="card.other_player"><div class="evidence-value"><span>{{ card.other_player }}</span><strong>{{ number(card.other_value ?? null) }}</strong></div><p>{{ card.other_scope }}</p></template>
      <details><summary>Scope, formula & limitations</summary><p v-if="card.formula">{{ card.formula }}</p><pre v-if="card.inputs">{{ JSON.stringify(card.inputs, null, 2) }}</pre><p v-for="note in card.limitations" :key="note">{{ note }}</p></details>
    </article></div>
    <details open class="honors-panel"><summary>Sources & coverage</summary>
      <div v-for="(source, i) in result.sources" :key="i" class="evidence-source"><a :href="safeLink(source.url)" target="_blank" rel="noopener noreferrer">{{ source.provider }} ↗</a><span>Retrieved {{ source.fetched_at }}</span><strong v-if="source.stale">Older cached data · refresh unavailable</strong></div>
      <p v-for="note in result.limitations" :key="note" class="picker-note">{{ note }}</p>
    </details>
    <details class="honors-panel"><summary>Numeric check history</summary><p v-for="(attempt, i) in result.verification.attempts" :key="i">Attempt {{ i + 1 }}: {{ attempt.valid ? 'Passed' : 'Needs correction' }}<template v-if="!attempt.valid"> — {{ JSON.stringify(attempt.errors) }}</template></p></details>
    <p class="evidence-disclaimer">{{ result.verification.note }}</p>
  </section>
</template>
