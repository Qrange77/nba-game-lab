<script setup lang="ts">
import { computed, ref } from 'vue'
import type { PlayerClarification } from '../types'
import { playerYears } from '../players'
const props = defineProps<{ groups: PlayerClarification[]; disabled: boolean }>()
const emit = defineEmits<{ resolve: [choices: Record<string, number>] }>()
const chosen = ref<Record<string, number>>({})
const complete = computed(() => props.groups.every(g => g.players.some(p => p.id === chosen.value[g.query])))
</script>
<template>
  <section class="identity-clarification" aria-label="Confirm player identities">
    <fieldset v-for="group in groups" :key="group.query" :disabled="disabled">
      <legend>Who did you mean by “{{ group.query }}”?</legend>
      <div class="identity-candidates"><label v-for="player in group.players" :key="player.id" class="identity-candidate" :class="{ selected: chosen[group.query] === player.id }">
        <input v-model="chosen[group.query]" type="radio" :name="`player-${group.query}`" :value="player.id" />
        <span><strong>{{ player.name }}</strong><small>{{ playerYears(player) }} · NBA ID {{ player.id }}</small></span>
      </label></div>
      <p v-if="!group.complete" class="picker-note">More matches exist. Use a full name or the player selector to narrow the search.</p>
      <p v-if="!group.players.length" class="picker-note">Use the player selector or send a corrected full name.</p>
    </fieldset>
    <button type="button" class="identity-continue" :disabled="disabled || !complete" @click="emit('resolve', { ...chosen })">Continue original question</button>
    <p v-if="disabled" class="picker-note">Only the latest pending question can be continued.</p>
  </section>
</template>
