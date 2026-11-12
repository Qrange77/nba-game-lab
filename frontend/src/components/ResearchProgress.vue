<script setup lang="ts">
import type { ResearchProgress } from '../types'
defineProps<{ research: ResearchProgress; pending: boolean }>()
const labels: Record<string, string> = { personal: 'Scoring production & efficiency', playoffs: 'Postseason scoring', honors: 'Career background', teammates: 'Bounded supporting-cast evidence', opponents: 'Finals competition context', era: 'Contemporaneous efficiency benchmarks', game: 'Archived game investigation' }
</script>

<template>
  <section class="research-progress" aria-label="Research plan and coverage">
    <div class="research-progress-heading"><strong>{{ pending ? 'Research in progress' : 'Research coverage' }}</strong><span v-if="research.elapsed_seconds">{{ Math.round(research.elapsed_seconds) }}s · {{ research.api_requests }} NBA API requests</span></div>
    <p v-if="research.scope" class="research-scope">{{ research.scope }}</p>
    <p v-if="research.criteria" class="research-criteria">{{ research.criteria }}</p>
    <ul class="research-tasks"><li v-for="task in research.tasks" :key="task.agent"><span class="activity-dot" :class="task.status === 'running' ? 'running' : task.status === 'completed' ? 'completed' : 'needs_evidence'"></span><div><strong>{{ labels[task.dimension] || task.dimension }}</strong><p>{{ task.question }}</p><small>{{ task.agent }} · Round {{ task.round }}</small></div><span class="research-task-status">{{ task.status }}</span></li></ul>
    <p v-if="research.coverage === 'partial'" class="research-coverage-note">Some evidence is incomplete. Read the report’s coverage and limitations before drawing an overall conclusion.</p>
    <p v-if="research.data_cutoff" class="research-cutoff">Research run: {{ new Date(research.data_cutoff).toLocaleString() }}. Source retrieval times may differ.</p>
  </section>
</template>

<style scoped>
.research-progress { border: 1px solid var(--color-border, #66708555); border-radius: 14px; padding: 18px; margin: 12px 0 20px; }
.research-progress-heading { display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:8px; }
.research-progress-heading span,.research-criteria,.research-cutoff,.research-tasks small { font-size:12px; opacity:.72; }
.research-scope { margin:10px 0 4px; font-size:14px; line-height:1.6; }
.research-criteria { margin:4px 0 12px; line-height:1.6; }
.research-tasks { list-style:none; padding:0; margin:12px 0 0; }
.research-tasks li { display:flex; align-items:flex-start; gap:10px; padding:12px 0; border-top:1px solid #66708533; }
.research-tasks .activity-dot { flex-shrink:0; margin-top:6px; }
.research-tasks li>div { flex:1; min-width:0; }
.research-tasks strong { font-size:13px; }
.research-tasks p { margin:4px 0; line-height:1.5; font-size:12px; opacity:.85; overflow-wrap:anywhere; }
.research-task-status { font-size:11px; text-transform:capitalize; padding:3px 6px; border-radius:6px; background:#66708522; }
.research-coverage-note { font-size:12px; line-height:1.6; color:#c98b38; }
.research-cutoff { margin-bottom:0; }
</style>
