<script setup lang="ts">
import { ref } from 'vue'
import { Users, X } from 'lucide-vue-next'
import PlayerPicker from './PlayerPicker.vue'
import type { PlayerChoice } from '../types'
const props = defineProps<{ modelValue: PlayerChoice[]; disabled: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [players: PlayerChoice[]] }>()
const expanded = ref(false)
function add(player: PlayerChoice | null) {
  if (!player || props.modelValue.some(p => p.id === player.id) || props.modelValue.length >= 8) return
  emit('update:modelValue', [...props.modelValue, player])
}
</script>
<template>
  <section class="research-players" aria-label="Research players">
    <div class="research-player-row">
      <button type="button" class="player-toggle" :aria-expanded="expanded" :disabled="disabled" @click="expanded = !expanded"><Users :size="15" /> Research players <span>{{ modelValue.length ? modelValue.length : 'Optional' }}</span></button>
      <span v-for="player in modelValue" :key="player.id" class="player-chip" :title="`NBA ID ${player.id}`">{{ player.name }}<button type="button" :aria-label="`Remove ${player.name}`" :disabled="disabled" @click="emit('update:modelValue', modelValue.filter(p => p.id !== player.id))"><X :size="13" /></button></span>
    </div>
    <div v-if="expanded" class="research-player-search">
      <PlayerPicker :model-value="null" clear-on-select label="Add a player" :disabled="disabled || modelValue.length >= 8" @update:model-value="add" />
      <p class="picker-note">Select up to eight players, or name them in your question. Ambiguous names require confirmation. You can change these selections during the conversation.</p>
    </div>
  </section>
</template>
