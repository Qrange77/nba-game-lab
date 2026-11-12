<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { Check, ChevronDown, GitBranch, LoaderCircle, Search, Sparkles, TriangleAlert, X } from 'lucide-vue-next'
import type { FlowNode, ResearchFlow, ResearchProgress, ToolCall } from '../types'
import { layoutFlow, NODE_HEIGHT, NODE_WIDTH } from '../researchFlow'

const props = defineProps<{ flow: ResearchFlow; calls: ToolCall[]; pending: boolean; research?: ResearchProgress }>()
const open = ref(props.pending)
const viewport = ref<HTMLElement | null>(null)
const root = ref<HTMLDetailsElement | null>(null)
const viewportWidth = ref(0)
const fitted = ref(false)
let observer: ResizeObserver | undefined
onMounted(() => { observer = new ResizeObserver(entries => { viewportWidth.value = entries[0]?.contentRect.width || 0 }); if (viewport.value) observer.observe(viewport.value) })
const selectedId = ref<string | null>(null)
const inspector = ref<HTMLElement | null>(null)
const following = ref(true)
watch(() => props.pending, (pending, wasPending) => {
  if (wasPending && !pending && following.value && !selectedId.value && props.flow.status !== 'failed' && props.flow.status !== 'interrupted') open.value = false
})
const now = ref(Date.now())
const receivedAt = ref(Date.now())
let timer: ReturnType<typeof setInterval> | undefined
watch(() => [props.flow.version, props.flow.status], () => {
  receivedAt.value = Date.now(); now.value = Date.now()
  if (timer) clearInterval(timer)
  if (props.flow.status === 'running') timer = setInterval(() => { now.value = Date.now() }, 500)
}, { immediate: true })
onBeforeUnmount(() => { if (timer) clearInterval(timer); observer?.disconnect() })
const graph = computed(() => layoutFlow(props.flow.nodes))
const scale = computed(() => fitted.value && viewportWidth.value ? Math.min(1, viewportWidth.value / graph.value.width) : 1)
const elapsed = computed(() => props.flow.elapsed_ms + (props.flow.status === 'running' ? now.value - receivedAt.value : 0))
const active = computed(() => props.flow.nodes.filter(node => node.status === 'running'))
const round = computed(() => Math.max(0, ...props.flow.nodes.map(node => node.round)))
const selected = computed(() => props.flow.nodes.find(node => node.id === selectedId.value))
const selectedCalls = computed(() => selected.value ? props.calls.filter(call => call.node_id === selected.value!.id || (call.id && selected.value!.tool_ids.includes(call.id))) : [])
const statusNames: Record<string, string> = { running: 'Running', completed: 'Completed', partial: 'Partial evidence', failed: 'Failed', queued: 'Queued', cancelled: 'Cancelled', interrupted: 'Connection interrupted', clarification: 'Needs clarification', outside_scope: 'Scope boundary' }
const summary = computed(() => props.flow.status === 'running' ? `${active.value.length} running${round.value ? ` · Round ${round.value}` : ''}` : `${statusNames[props.flow.status] || props.flow.status}${round.value ? ` · ${round.value} round${round.value === 1 ? '' : 's'}` : ''}`)
function duration(ms: number) { return ms < 1000 ? '<1s' : `${(ms / 1000).toFixed(ms < 10000 ? 1 : 0)}s` }
function nodeDuration(node: FlowNode) { return node.started_ms == null ? 'Not started' : duration(Math.max(0, (node.ended_ms ?? elapsed.value) - node.started_ms)) }
async function select(node: FlowNode) {
  selectedId.value = selectedId.value === node.id ? null : node.id; following.value = false
  await nextTick()
  if (selectedId.value) inspector.value?.scrollIntoView({block:'nearest'})
}
function format(value: unknown) {
  if (typeof value === 'string') { try { return JSON.stringify(JSON.parse(value), null, 2) } catch { return value } }
  return JSON.stringify(value, null, 2)
}
async function follow() { following.value = true; await nextTick(); if (viewport.value) viewport.value.scrollLeft = viewport.value.scrollWidth }
watch(() => props.flow.nodes.length, async () => {
  if (following.value && open.value && props.pending) {
    await follow()
    const area = root.value?.closest('.conversation-scroll')
    if (area && root.value) area.scrollTop += root.value.getBoundingClientRect().top - area.getBoundingClientRect().top - 12
  }
})
watch(() => props.flow.status, async status => {
  if (status !== 'running' && following.value && round.value > 1) { fitted.value = true; await nextTick(); if (viewport.value) viewport.value.scrollLeft = 0 }
})
const expandedTools = ref(new Set<string>())
function toolToggle(event: Event, id: string) {
  const next = new Set(expandedTools.value)
  if ((event.target as HTMLDetailsElement).open) next.add(id); else next.delete(id)
  expandedTools.value = next
}
</script>

<template>
  <details ref="root" class="research-flow" :open="open" @toggle="open = ($event.target as HTMLDetailsElement).open">
    <summary class="flow-heading">
      <GitBranch :size="17" /><strong>Research workspace</strong>
      <span class="flow-summary" role="status">{{ summary }}</span><ChevronDown :size="16" class="flow-chevron" />
    </summary>
    <div class="flow-body">
      <div class="flow-toolbar"><span>Live execution graph</span><span>{{ duration(elapsed) }}<template v-if="flow.peak_parallel"> · Peak {{ flow.peak_parallel }} concurrent researchers</template></span></div>
      <p v-if="research?.scope" class="flow-scope">{{ research.scope }}</p>
      <div class="flow-legend"><span><i class="legend-dot running"></i>Running</span><span><i class="legend-dot completed"></i>Completed</span><span><i class="legend-dot partial"></i>Partial / failed</span><div class="flow-controls"><button type="button" :aria-pressed="fitted" @click="fitted = !fitted">{{ fitted ? 'Actual size' : 'Fit graph' }}</button><button v-if="pending" type="button" :aria-pressed="following" @click="follow">{{ following ? 'Following live' : 'Follow live' }}</button></div></div>
      <div ref="viewport" class="flow-viewport" role="group" aria-label="Research execution graph" tabindex="0">
        <div class="flow-stage" :style="{width: `${graph.width * scale}px`, height: `${graph.height * scale}px`}">
        <div class="flow-canvas" :style="{width: `${graph.width}px`, height: `${graph.height}px`, transform: `scale(${scale})`}">
          <svg class="flow-edges" :width="graph.width" :height="graph.height" aria-hidden="true">
            <path v-for="edge in graph.edges" :key="edge.id" :d="edge.path" :class="['flow-edge', edge.status]" />
          </svg>
          <TransitionGroup name="flow-node">
            <button v-for="node in graph.nodes" :key="node.id" type="button" :class="['flow-node', node.status, {selected: selectedId === node.id}]"
              :style="{left: `${node.x}px`, top: `${node.y}px`, width: `${NODE_WIDTH}px`, height: `${NODE_HEIGHT}px`}" :aria-pressed="selectedId === node.id" :aria-label="`${node.label}${node.round ? `, round ${node.round}` : ''}, ${statusNames[node.status]}. Inspect task and tools`" @click="select(node)">
              <span class="flow-node-title"><LoaderCircle v-if="node.status === 'running'" :size="14" class="node-spinner" /><Check v-else-if="node.status === 'completed'" :size="14" /><TriangleAlert v-else-if="['partial','failed','interrupted'].includes(node.status)" :size="14" /><Search v-else-if="node.role === 'researcher'" :size="14" /><Sparkles v-else :size="14" /><strong>{{ node.label }}</strong></span>
              <span class="flow-node-meta">{{ node.round ? `Round ${node.round} · ` : '' }}{{ statusNames[node.status] }}</span>
              <span class="flow-node-time">{{ nodeDuration(node) }}</span>
            </button>
          </TransitionGroup>
        </div>
        </div>
      </div>
      <p class="flow-hint">Branches share the same stage; each updates independently. Scroll horizontally to explore later rounds. Select a node to inspect its task and tools.</p>
      <section v-if="selected" ref="inspector" class="flow-inspector" aria-label="Selected research node">
        <div class="inspector-heading"><strong>{{ selected.label }}<span v-if="selected.round"> · Round {{ selected.round }}</span></strong><button type="button" aria-label="Close node details" @click="selectedId = null"><X :size="16" /></button></div>
        <p class="inspector-agent">{{ selected.agent }} · {{ statusNames[selected.status] }} · {{ nodeDuration(selected) }}</p>
        <p>{{ selected.description }}</p><p v-if="selected.summary" class="inspector-summary">{{ selected.summary }}</p>
        <p v-if="selected.started_ms != null" class="inspector-timing">Started +{{ (selected.started_ms / 1000).toFixed(2) }}s<template v-if="selected.ended_ms != null"> · Ended +{{ (selected.ended_ms / 1000).toFixed(2) }}s</template> from run start</p>
        <p v-if="!selectedCalls.length" class="flow-hint">No tool calls recorded for this node{{ selected.status === 'running' ? ' yet' : '' }}.</p>
        <details v-for="(call, index) in selectedCalls" :key="call.id || index" class="node-tool" @toggle="toolToggle($event, call.id || `${selected.id}-${index}`)">
          <summary><span>{{ call.name.replaceAll('_', ' ') }}</span><small>{{ call.status || 'completed' }}</small></summary>
          <div v-if="expandedTools.has(call.id || `${selected.id}-${index}`)"><strong>Arguments</strong><pre>{{ format(call.args) }}</pre><strong>Result</strong><pre>{{ call.result == null ? 'Waiting for the tool result.' : format(call.result) }}</pre></div>
        </details>
      </section>
      <p v-if="flow.status === 'partial'" class="flow-warning">Some source coverage remains incomplete. Read the report's evidence limits.</p>
      <p v-if="flow.status === 'failed' || flow.status === 'interrupted'" class="flow-warning">{{ flow.status === 'interrupted' ? 'Live updates stopped. Check conversation history for the saved outcome.' : 'The run stopped before completion. Completed work remains visible; active work was not marked successful.' }}</p>
    </div>
  </details>
</template>

<style scoped>
.research-flow { --flow-line:#66708555; --flow-active:#7b8dff; --flow-done:#56bd98; border:1px solid var(--color-border, #66708555); border-radius:14px; margin:12px 0 20px; overflow:hidden; background:color-mix(in srgb, currentColor 2%, transparent); }
.flow-heading { display:flex; align-items:center; gap:9px; padding:15px 16px; cursor:pointer; list-style:none; font-size:13px; }
.flow-heading::-webkit-details-marker { display:none; }
.flow-heading>svg:first-child { color:var(--flow-active); flex-shrink:0; }
.flow-summary { margin-left:auto; font-size:11px; opacity:.75; }
.flow-chevron { transition:transform .2s; flex-shrink:0; }
.research-flow[open] .flow-chevron { transform:rotate(180deg); }
.flow-body { border-top:1px solid var(--flow-line); padding:14px 14px 8px; }
.flow-toolbar,.flow-legend { display:flex; align-items:center; flex-wrap:wrap; gap:8px 14px; font-size:10px; }
.flow-toolbar { justify-content:space-between; text-transform:uppercase; letter-spacing:.04em; opacity:.75; }
.flow-scope { margin:10px 0; font-size:12px; line-height:1.6; }
.flow-legend { margin:12px 0 4px; }
.flow-legend span { display:flex; align-items:center; gap:5px; }
.legend-dot { width:6px; height:6px; border-radius:50%; background:#d3a05c; }
.legend-dot.running { background:var(--flow-active); }
.legend-dot.completed { background:var(--flow-done); }
.flow-controls { display:flex; gap:6px; margin-left:auto; }
.flow-legend button { color:var(--flow-active); border:1px solid var(--flow-line); border-radius:5px; padding:4px 7px; cursor:pointer; }
.flow-viewport { overflow-x:auto; border-radius:10px; margin:5px -6px; scrollbar-width:thin; background-image:radial-gradient(var(--flow-line) .65px, transparent .65px); background-size:16px 16px; }
.flow-stage { position:relative; min-width:100%; }
.flow-canvas { position:relative; min-width:100%; transform-origin:top left; }
.flow-edges { position:absolute; inset:0; overflow:visible; pointer-events:none; }
.flow-edge { fill:none; stroke:var(--flow-line); stroke-width:1.5; }
.flow-edge.running { stroke:var(--flow-active); stroke-dasharray:5 5; animation:edge-travel 1s linear infinite; }
.flow-edge.partial,.flow-edge.failed,.flow-edge.interrupted { stroke:#c98b38; }
.flow-node { position:absolute; display:flex; flex-direction:column; align-items:flex-start; justify-content:center; padding:10px; text-align:left; border:1px solid var(--flow-line); border-radius:10px; background:var(--surface-raised, #fff); color:var(--ink, inherit); cursor:pointer; transition:left .3s, top .3s, border-color .2s; }
.flow-node.running { border-color:var(--flow-active); box-shadow:0 0 0 2px #7b8dff12; }
.flow-node.completed { border-color:#56bd9855; }
.flow-node.partial,.flow-node.failed,.flow-node.interrupted { border-color:#c98b3877; }
.flow-node.queued,.flow-node.cancelled { border-style:dashed; }
.flow-node.selected { outline:2px solid var(--flow-active); outline-offset:3px; }
.flow-node:focus-visible,.flow-heading:focus-visible,.flow-viewport:focus-visible { outline:2px solid var(--flow-active); outline-offset:2px; }
.flow-node-title { display:flex; gap:5px; align-items:center; font-size:11px; width:100%; }
.flow-node-title svg { flex-shrink:0; color:var(--flow-active); }
.flow-node-title strong { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.completed .flow-node-title svg { color:var(--flow-done); }
.flow-node-meta { margin:5px 0 2px; font-size:10px; opacity:.7; }
.flow-node-time { font-size:9px; opacity:.55; }
.node-spinner { animation:node-spin 1.3s linear infinite; }
.flow-node-enter-active { transition:opacity .25s, transform .25s; }
.flow-node-enter-from { opacity:0; transform:scale(.94); }
.flow-hint { font-size:10px; line-height:1.7; opacity:.65; margin:8px 0; }
.flow-inspector { border:1px solid var(--flow-line); border-radius:10px; padding:12px; margin:12px 0; font-size:12px; line-height:1.65; }
.inspector-heading { display:flex; align-items:center; justify-content:space-between; gap:8px; }
.inspector-heading button { cursor:pointer; padding:4px; }
.inspector-agent,.inspector-timing { font-size:10px; opacity:.65; }
.inspector-summary { border-left:2px solid var(--flow-active); padding-left:10px; }
.node-tool { border-top:1px solid var(--flow-line); margin-top:8px; padding:8px 0 0; }
.node-tool summary { cursor:pointer; display:flex; justify-content:space-between; gap:8px; font-size:11px; }
.node-tool small { opacity:.6; }
.node-tool strong { display:block; font-size:10px; margin:8px 0 3px; }
.node-tool pre { white-space:pre-wrap; overflow-wrap:anywhere; font-size:10px; max-height:240px; overflow:auto; background:#66708512; padding:8px; border-radius:5px; }
.flow-warning { color:#b97b2b; font-size:11px; line-height:1.7; }
@keyframes edge-travel { to { stroke-dashoffset:-20; } }
@keyframes node-spin { to { transform:rotate(360deg); } }
@media (prefers-reduced-motion:reduce) { *,*::before,*::after { animation:none !important; transition:none !important; } }
@media (max-width:480px) { .flow-heading { padding:13px 10px; gap:6px; } .flow-heading strong { font-size:12px; } .flow-summary { font-size:10px; } .flow-body { padding:12px 8px 6px; } }
</style>
