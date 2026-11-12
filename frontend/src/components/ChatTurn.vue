<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { ArrowUpRight, CircleAlert, Terminal, ChevronDown } from 'lucide-vue-next'
import ResultPanel from './ResultPanel.vue'
import EvidenceSummary from './EvidenceSummary.vue'
import PlayerClarification from './PlayerClarification.vue'
import ResearchProgress from './ResearchProgress.vue'
import ResearchFlow from './ResearchFlow.vue'
import ScoringContext from './ScoringContext.vue'
import ScopeClarification from './ScopeClarification.vue'
import { clarificationPrompt } from '../clarification'
import { renderMarkdown } from '../markdown'
import { reportSections } from '../reportSections'
import type { Panel, Turn, ToolCall } from '../types'
const props = defineProps<{ turn: Turn; pending: boolean; canResolve?: boolean }>()
const thinkingOpen = ref(props.pending)
watch(() => props.pending, value => { if (!value) thinkingOpen.value = false })
watch(() => !!props.turn.research_flow, value => { if (value) thinkingOpen.value = false })
function toggleThinking(event: Event) { thinkingOpen.value = (event.target as HTMLDetailsElement).open }
const toolLabels: Record<string, string> = {
  plan_research: 'Planning independent investigations', review_research: 'Checking findings and research gaps',
  clarify_research: 'Clarifying comparison period and criteria',
  confirm_scoring_contract: 'Confirming the scoring claim and comparison rules',
  finish_blocked: 'Requiring follow-up evidence before closing research',
  repair_research_plan: 'Repairing the plan to match the approved comparison',
  repair_scoring_scope: 'Checking the explicit season-window lengths',
  recheck_scoring_scope: 'Checking the completed-season cutoff',
  collect_scoring_profile: 'Retrieving comparable scoring records',
  collect_scoring_environment: 'Verifying contemporaneous shooting benchmarks',
  collect_scoring_support: 'Investigating core helpers and rotation samples',
  collect_scoring_finals: 'Verifying Finals scoring and opposition',
  review_content_evidence: 'Checking whether the findings answer the research question',
  inspect_supporting_cast: 'Investigating supporting-cast sample adequacy',
  compose_scoring_review: 'Checking the answer and its numerical evidence',
  query_career_profile: 'Discovering career seasons and achievements', query_supporting_cast: 'Investigating core helpers and rotation',
  query_finals_path: 'Verifying Finals appearances and opponents', query_era_environment: 'Comparing contemporaneous league conditions',
  query_game_context: 'Checking both teams’ box scores and efficiency',
  verify_report: 'Checking report numbers and citations',
  review_report: 'Reviewing interpretation against retrieved evidence',
  compare_awards: 'Comparing honors', player_awards: 'Looking up honors', resolve_player: 'Identifying a player',
  query_performance_context: 'Checking season ranks, team offense and opponent performance',
  query_evidence: 'Retrieving evidence', compare_players: 'Comparing player statistics',
  plan_team_context_research: 'Selecting relevant seasons', research_team_context: 'Investigating both supporting casts',
  query_competitive_context: 'Checking teammates and roles', compare_competitive_context: 'Comparing key teammates and support',
  submit_answer: 'Checking historical numeric claims',
  find_counterexamples: 'Searching for counterexamples', find_comparative_edges: 'Comparing strengths and weaknesses',
  resolve_evidence_references: 'Matching evidence references', validate_response: 'Checking response format',
  verified_context_fallback: 'Preparing verified team facts', verified_honors_fallback: 'Preparing verified honors',
}
defineEmits<{ retry: []; resolve: [choices: Record<string, number>]; answer: [message: string] }>()
const clarification = computed(() => clarificationPrompt(props.turn))
const copyStatus = ref('')
function activityState(call: ToolCall) {
  return call.status || 'completed'
}
function activityLabel(call: ToolCall) {
  try {
    const result = typeof call.result === 'string' ? JSON.parse(call.result) : call.result
    if (result?.failure_type === 'format') return 'Format needs repair'
    if (result?.failure_type === 'citation') return 'Citations need repair'
  } catch { /* Fall back to the execution status. */ }
  return { running: 'Running', completed: 'Completed', failed: 'Failed', needs_evidence: 'Needs evidence', needs_revision: 'Needs revision' }[activityState(call)]
}
async function copyReply() {
  try { await navigator.clipboard.writeText(props.turn.response); copyStatus.value = 'Copied' }
  catch { copyStatus.value = 'Copy unavailable. Select the reply to copy it.' }
}
const answerSections = computed(() => reportSections(props.turn.response).map(section => ({ ...section, html: renderMarkdown(section.source) })))
const panels = computed<Panel[]>(() => props.turn.tool_calls.flatMap(call => {
  if (call.name !== 'display_panel') return []
  try {
    const result = typeof call.result === 'string' ? JSON.parse(call.result) : call.result
    if (!result || result.error || result.message || (!result.player && !result.team)) return []
    return [result as Panel]
  } catch { return [] }
}))
</script>

<template>
  <div class="chat-turn">
    <div class="user-message"><span class="message-label">YOU</span><div class="user-bubble">{{ turn.message }}</div></div>
    <article class="assistant-message">
      <div class="assistant-heading"><img src="/favicon.svg" width="27" height="27" alt="" /><strong>Game Lab</strong><span>ASSISTANT</span></div>
      <ResearchFlow v-if="turn.research_flow" :flow="turn.research_flow" :calls="turn.tool_calls" :pending="pending" :research="turn.research || turn.evidence_result?.research" />
      <ResearchProgress v-else-if="turn.research || turn.evidence_result?.research" :research="(turn.research || turn.evidence_result?.research)!" :pending="pending" />
      <details v-if="pending || turn.tool_calls.length" class="tool-log thinking-log" :open="thinkingOpen" @toggle="toggleThinking">
        <summary><Terminal :size="14" /><strong>Research activity</strong><span v-if="turn.tool_calls.length">· {{ turn.tool_calls.length }} tool {{ turn.tool_calls.length === 1 ? 'call' : 'calls' }}</span><span v-if="pending" class="activity-dot running" aria-label="In progress"></span><ChevronDown :size="14" /></summary>
        <p v-if="pending" class="thinking" role="status">{{ turn.activity_phase || 'Preparing your request' }}</p>
        <p v-if="pending && !turn.tool_calls.length" class="thinking-detail">Tool activity will appear here as it happens.</p>
        <details v-for="(call, index) in turn.tool_calls" :key="call.id || index" class="tool-entry">
          <summary><span class="activity-dot" :class="activityState(call)"></span><span>{{ toolLabels[call.name] || call.name.replaceAll('_', ' ') }}<small class="activity-name">{{ call.agent ? `${call.agent} · ` : '' }}{{ call.name }}</small></span><span class="activity-status">{{ activityLabel(call) }}</span></summary>
          <strong class="activity-section-label">Input</strong><pre>{{ JSON.stringify(call.args, null, 2) }}</pre>
          <template v-if="call.result !== undefined"><strong class="activity-section-label">Result</strong><pre>{{ typeof call.result === 'string' ? call.result : JSON.stringify(call.result, null, 2) }}</pre></template>
          <p v-else class="thinking-detail">Waiting for the tool…</p>
        </details>
      </details>
      <div v-if="!pending && turn.failed" class="send-error" role="alert"><CircleAlert :size="18" /><div><strong>Message couldn't be completed</strong><p>{{ turn.response }}</p><button class="text-button" @click="$emit('retry')">Try again <ArrowUpRight :size="15" /></button></div></div>
      <template v-else-if="!pending">
        <ScopeClarification v-if="clarification" :prompt="clarification" :disabled="!canResolve" @answer="$emit('answer', $event)" />
        <template v-for="(section, index) in (clarification ? [] : answerSections)" :key="index">
          <details v-if="section.collapsed" class="answer-details"><summary>{{ section.title }}</summary><div class="answer-content" v-html="section.html"></div></details>
          <div v-else class="answer-content" v-html="section.html"></div>
        </template>
        <ScoringContext v-if="turn.evidence_result?.scoring" :review="turn.evidence_result.scoring" />
        <PlayerClarification v-if="turn.player_clarifications?.length" :groups="turn.player_clarifications" :disabled="!canResolve" @resolve="$emit('resolve', $event)" />
        <button v-if="!turn.player_clarifications?.length" type="button" class="copy-reply" @click="copyReply">Copy reply</button><span v-if="copyStatus" class="copy-status" role="status">{{ copyStatus }}</span>
        <EvidenceSummary v-if="turn.evidence_result" :result="turn.evidence_result" />
        <ResultPanel v-for="(panel, index) in panels" :key="index" :panel="panel" />
      </template>
    </article>
  </div>
</template>

<style scoped>
.answer-details { margin:12px 0; padding:12px 16px; border:1px solid #66708544; border-radius:10px; }
.answer-details>summary { cursor:pointer; font-size:13px; font-weight:600; }
.answer-details[open]>summary { margin-bottom:12px; }
</style>
