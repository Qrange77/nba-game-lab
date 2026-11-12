<script setup lang="ts">
import type { ScoringReview } from '../types'
defineProps<{ review: ScoringReview }>()
function value(v: number | null | undefined) { return v == null ? 'Unavailable' : v.toLocaleString('en-US', {maximumFractionDigits:2}) }
function safeEvidence(url: string | null | undefined) { return url && /^\/sessions\/[a-f0-9-]+\/evidence\/ev_[a-f0-9]{20}$/.test(url) ? url : undefined }
</script>

<template>
  <section v-if="review.support_samples.length" class="support-context" aria-label="Supporting-cast sample details">
    <h3>Supporting-cast sample details</h3>
    <p>Core helpers are considered first. These rotation samples retain contemporary production, minutes and recorded appearances; they do not establish injury causes or a full-career teammate ranking.</p>
    <details v-for="sample in review.support_samples" :key="`${sample.player_name}-${sample.season}-${sample.phase}-${sample.gap_id || 'initial'}`">
      <summary>{{ sample.player_name }} · {{ sample.season }}–{{ String(sample.season + 1).slice(-2) }} · {{ sample.phase }}<span v-if="sample.followup" class="followup-badge">Follow-up</span></summary>
      <p v-if="sample.followup_reason"><strong>Why this sample was added:</strong> {{ sample.followup_reason }}</p>
      <p>{{ sample.selection }}</p>
      <div class="rotation-scroll"><table><thead><tr><th>Teammate</th><th>Role in sample</th><th>PPG</th><th>MPG</th><th>GP</th><th>TS%</th><th>Evidence</th></tr></thead><tbody>
        <tr v-for="record in sample.rotation_records" :key="record.id"><td>{{ record.player_name }}</td><td>{{ sample.core.includes(record.id) ? 'Core candidate' : 'Rotation' }}</td><td>{{ value(record.values.PTS?.value) }}</td><td>{{ value(record.values.MIN?.value) }}</td><td>{{ value(record.values.GP?.value) }}</td><td>{{ value(record.values.TS_PCT?.value) }}</td><td><a v-if="safeEvidence(record.evidence_url)" :href="safeEvidence(record.evidence_url)" target="_blank" rel="noopener noreferrer">Inspect source ↗</a><span v-else>See evidence panel</span></td></tr>
      </tbody></table></div>
    </details>
  </section>
</template>

<style scoped>
.support-context { margin:24px 0; font-size:13px; }
.support-context>p,.support-context details>p { opacity:.75; line-height:1.7; }
.support-context details { border:1px solid #66708544; border-radius:10px; margin-top:10px; padding:12px; }
.support-context summary { cursor:pointer; font-weight:600; }
.followup-badge { margin-left:8px; font-size:10px; color:#809bff; border:1px solid #809bff55; border-radius:5px; padding:2px 5px; }
.rotation-scroll { overflow-x:auto; }
.rotation-scroll table { width:100%; min-width:620px; border-collapse:collapse; font-size:12px; }
.rotation-scroll th,.rotation-scroll td { text-align:left; padding:10px 8px; border-bottom:1px solid #66708533; }
.rotation-scroll a { color:#809bff; }
</style>
