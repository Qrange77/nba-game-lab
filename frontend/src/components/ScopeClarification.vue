<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowRight, Check, MessageSquare } from 'lucide-vue-next'
import { seasonLabel, windowReply } from '../clarification'
import type { ClarificationPrompt } from '../clarification'

const props = defineProps<{ prompt: ClarificationPrompt; disabled: boolean }>()
const emit = defineEmits<{ answer: [message: string] }>()
const mode = ref<'choices' | 'windows' | 'custom'>(props.prompt.kind === 'custom' ? 'custom' : 'choices')
const years = ref(['', '', '', ''])
const custom = ref('')
const error = ref('')
const submitting = ref(false)
const locked = computed(() => props.disabled || submitting.value)
const preview = computed(() => windowReply(props.prompt.players, years.value, props.prompt.cutoff))
function submit(message: string) {
  if (locked.value || !message.trim()) return
  submitting.value = true
  emit('answer', message.trim())
}
function submitWindows() {
  error.value = preview.value.error
  if (!error.value) submit(preview.value.message)
}
function choose(next: 'choices' | 'windows' | 'custom') { mode.value = next; error.value = '' }
</script>

<template>
  <section class="clarification-card" aria-label="Research clarification">
    <div class="card-heading"><MessageSquare :size="18" /><strong>{{ disabled ? 'Clarification' : 'Your choice' }}</strong><span>{{ disabled ? 'Inactive' : 'Waiting for your answer' }}</span></div>
    <p class="question">{{ prompt.question }}</p>
    <fieldset :disabled="locked">
      <legend class="sr-only">Choose how to continue</legend>
      <div v-if="mode === 'choices'" class="options">
        <template v-if="prompt.kind === 'period'">
          <button type="button" class="option" @click="submit('Use complete careers for both players, preserving the requested research dimensions.')"><span class="option-number">1</span><span><strong>Complete careers</strong><small>Use all supported completed seasons. Start research.</small></span><ArrowRight :size="18" /></button>
          <button type="button" class="option" @click="choose('windows')"><span class="option-number">2</span><span><strong>Choose season windows</strong><small>Enter an equal number of seasons for each player.</small></span><ArrowRight :size="18" /></button>
        </template>
        <template v-else-if="prompt.kind === 'influence'">
          <button type="button" class="option" @click="submit('I mean observed scoring performance, not overall or causal impact.')"><span class="option-number">1</span><span><strong>Scoring performance</strong><small>Compare scoring evidence; choose the period next if needed.</small></span><ArrowRight :size="18" /></button>
          <button type="button" class="option" @click="submit('I mean observed on-court contributions: offense, playmaking, defensive evidence and team on/off, not causal winning impact.')"><span class="option-number">2</span><span><strong>On-court contributions</strong><small>Research several dimensions with coverage and causal limits.</small></span><ArrowRight :size="18" /></button>
          <button type="button" class="option" @click="submit('I mean cultural and commercial influence, not scoring performance.')"><span class="option-number">3</span><span><strong>Cultural / commercial influence</strong><small>Outside this research tool's coverage.</small></span><ArrowRight :size="18" /></button>
        </template>
        <button type="button" class="custom-choice" @click="choose('custom')">Write my own answer</button>
      </div>
      <form v-else-if="mode === 'windows'" @submit.prevent="submitWindows">
        <p class="hint">Enter season start years: 1990 means 1990-91. Supported through {{ seasonLabel(prompt.cutoff) }}.</p>
        <div class="player-window" v-for="(player, index) in prompt.players" :key="player">
          <strong>{{ player }}</strong>
          <div class="year-fields"><label>Start year<input v-model="years[index * 2]" type="number" step="1" min="1984" :max="prompt.cutoff" required :aria-label="`${player} start year`" placeholder="YYYY" /></label><label>End year<input v-model="years[index * 2 + 1]" type="number" step="1" min="1984" :max="prompt.cutoff" required :aria-label="`${player} end year`" placeholder="YYYY" /></label></div>
        </div>
        <p v-if="error" class="validation" role="alert">{{ error }}</p>
        <div class="actions"><button type="button" class="custom-choice" @click="choose('choices')">Back</button><button type="submit" class="continue"><Check :size="16" />Confirm windows</button></div>
      </form>
      <form v-else @submit.prevent="submit(custom)">
        <label class="custom-label">Your answer<textarea v-model="custom" rows="3" maxlength="2000" placeholder="Describe the scope you want to compare…" required /></label>
        <div class="actions"><button v-if="prompt.kind !== 'custom'" type="button" class="custom-choice" @click="choose('choices')">Back</button><button type="submit" class="continue" :disabled="!custom.trim()">Continue<ArrowRight :size="16" /></button></div>
      </form>
    </fieldset>
    <p v-if="disabled" class="hint">Use the latest question or the message box to continue.</p>
  </section>
</template>

<style scoped>
.clarification-card { margin:20px 0; padding:22px; border:1px solid #64748b66; border-radius:18px; background:#64748b0b; }
.card-heading { display:flex; gap:9px; align-items:center; color:var(--text-primary,inherit); }
.card-heading>svg { color:#818cf8; }.card-heading>span { margin-left:auto; font-size:12px; opacity:.65; }
.question { line-height:1.65; margin:16px 0; }.clarification-card fieldset { border:0; padding:0; margin:0; min-width:0; }
.options { display:grid; gap:10px; }.option { display:flex; align-items:center; gap:14px; width:100%; text-align:left; border:1px solid #64748b55; border-radius:12px; padding:15px; background:transparent; color:inherit; cursor:pointer; }
.option:hover:not(:disabled) { border-color:#818cf8; background:#6366f111; }.option:focus-visible,.continue:focus-visible,.custom-choice:focus-visible { outline:2px solid #818cf8; outline-offset:3px; }
.option>span:nth-child(2) { flex:1; }.option strong,.option small { display:block; }.option small { margin-top:5px; line-height:1.5; opacity:.7; }.option-number { display:grid; place-items:center; border:1px solid #64748b66; border-radius:7px; width:28px; height:28px; flex-shrink:0; font-size:13px; }
.custom-choice { color:inherit; opacity:.8; background:transparent; border:0; padding:10px 0; text-align:left; cursor:pointer; font-size:13px; }.hint { font-size:12px; line-height:1.6; opacity:.7; }
.player-window { margin:16px 0; }.player-window>strong { font-size:14px; }.year-fields { display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-top:10px; }
label { display:grid; gap:7px; font-size:12px; }input,textarea { min-width:0; width:100%; box-sizing:border-box; padding:11px; border:1px solid #64748b77; border-radius:8px; background:transparent; color:inherit; font:inherit; font-size:14px; }textarea { resize:vertical; }
.actions { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-top:15px; }.continue { margin-left:auto; display:flex; gap:8px; align-items:center; background:#4f46e5; color:white; border:0; border-radius:9px; padding:11px 16px; cursor:pointer; }
fieldset:disabled { opacity:.55; }button:disabled { cursor:not-allowed; }.continue:disabled { opacity:.5; }.validation { color:#ef6666; font-size:13px; }
@media(max-width:520px) { .clarification-card { padding:16px; }.card-heading { flex-wrap:wrap; }.card-heading>span { margin-left:0; width:100%; }.option { padding:12px; } }
</style>
