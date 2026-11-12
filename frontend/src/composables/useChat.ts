import { computed, ref } from 'vue'
import type { Conversation, Session, Turn, EvidenceResult, PlayerChoice, PlayerClarification, ToolCall, ResearchTask, ResearchProgress, ResearchFlow } from '../types'
import { acceptFlow, interruptFlow } from '../researchFlow'

type ChatResult = { session_id: string; response: string; tool_calls: ToolCall[]; evidence_result?: EvidenceResult; research_flow?: ResearchFlow | null; selected_players: PlayerChoice[]; player_clarifications: PlayerClarification[]; failed?: boolean }
type ChatEvent = { type: 'phase'; label: string } | { type: 'session'; session_id: string } | { type: 'players'; players: PlayerChoice[] } |
  ({ type: 'research_plan' } & ResearchProgress) | { type: 'research_task'; task: ResearchTask } |
  { type: 'research_flow'; flow: ResearchFlow } |
  { type: 'tool_start' | 'tool_end'; call: ToolCall } | { type: 'done'; data: ChatResult } |
  { type: 'error'; message: string }

async function streamChat(body: unknown, onEvent: (event: ChatEvent) => void): Promise<ChatResult> {
  const response = await fetch('/chat/stream', {
    method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' }, body: JSON.stringify(body),
  })
  if (!response.ok) {
    const error = await response.json().catch(() => null)
    throw new Error(typeof error?.detail === 'string' ? error.detail : `Request failed (${response.status})`)
  }
  if (!response.body) throw new Error('Live updates are unavailable in this browser.')
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (true) {
      const { value, done } = await reader.read()
      buffer += decoder.decode(value, { stream: !done })
      let boundary: number
      while ((boundary = buffer.indexOf('\n\n')) !== -1) {
        const block = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        const data = block.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n')
        if (!data) continue
        const event = JSON.parse(data) as ChatEvent
        if (event.type === 'error') throw new Error(event.message)
        onEvent(event)
        if (event.type === 'done') return event.data
      }
      if (done) throw new Error('Live connection ended before the reply completed. The conversation may still finish saving; check history before retrying.')
    }
  } finally {
    await reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, options)
  const data = await response.json().catch(() => null)
  if (!response.ok) throw new Error(typeof data?.detail === 'string' ? data.detail : `Request failed (${response.status})`)
  if (data === null) throw new Error('The server returned an unreadable response.')
  return data as T
}

export function useChat() {
  const selectedPlayers = ref<PlayerChoice[]>([])
  const sessions = ref<Session[]>([])
  const turns = ref<Turn[]>([])
  const sessionId = ref<string | null>(null)
  const title = ref('New conversation')
  const sending = ref(false)
  const loadingSession = ref(false)
  const loadingHistory = ref(false)
  const deletingId = ref<string | null>(null)
  const deleteError = ref('')
  const historyError = ref('')
  const error = ref('')
  // The initial history request establishes the browser's ownership cookie.
  const busy = computed(() => sending.value || loadingSession.value || loadingHistory.value || deletingId.value !== null)

  async function refreshHistory() {
    loadingHistory.value = true
    historyError.value = ''
    try { sessions.value = await request<Session[]>('/sessions') }
    catch (e) { historyError.value = e instanceof Error ? e.message : 'Unable to load history.' }
    finally { loadingHistory.value = false }
  }

  function newChat() {
    if (busy.value) return
    selectedPlayers.value = []
    sessionId.value = null
    turns.value = []
    title.value = 'New conversation'
    error.value = ''
  }

  async function openSession(id: string) {
    if (busy.value) return false
    loadingSession.value = true
    error.value = ''
    try {
      const record = await request<Conversation>(`/sessions/${encodeURIComponent(id)}`)
      selectedPlayers.value = record.selected_players || []
      sessionId.value = record.session_id
      title.value = record.title
      turns.value = record.turns
      return true
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Unable to open this conversation.'
      return false
    } finally { loadingSession.value = false }
  }

  async function deleteSession(id: string) {
    if (busy.value) return false
    deletingId.value = id
    deleteError.value = ''
    try {
      await request(`/clear?session_id=${encodeURIComponent(id)}`, { method: 'POST' })
      sessions.value = sessions.value.filter(session => session.session_id !== id)
      if (sessionId.value === id) {
        sessionId.value = null
        turns.value = []
        title.value = 'New conversation'
        selectedPlayers.value = []
        error.value = ''
      }
      return true
    } catch (e) {
      deleteError.value = `Couldn't delete conversation. ${e instanceof Error ? e.message : 'Please try again.'}`
      return false
    } finally { deletingId.value = null }
  }

  async function send(message: string, identityChoices?: Record<string, number>) {
    if (busy.value || !message.trim()) return
    sending.value = true
    error.value = ''
    const turn: Turn = { message: message.trim(), response: '', tool_calls: [] }
    const resume = !!identityChoices && !!turns.value.at(-1)?.player_clarifications?.length
    if (resume) turns.value[turns.value.length - 1] = turn
    else turns.value.push(turn)
    const index = turns.value.length - 1
    try {
      const data = await streamChat({ message: turn.message, session_id: sessionId.value,
        player_ids: selectedPlayers.value.map(p => p.id), identity_choices: identityChoices || {}, resume_pending: resume }, event => {
        const active = turns.value[index]!
        if (event.type === 'phase') active.activity_phase = event.label
        if (event.type === 'session') sessionId.value = event.session_id
        if (event.type === 'players') selectedPlayers.value = event.players
        if (event.type === 'research_flow') active.research_flow = acceptFlow(active.research_flow, event.flow)
        if (event.type === 'research_plan') active.research = { scope: event.scope, criteria: event.criteria, tasks: event.tasks }
        if (event.type === 'research_task' && active.research) {
          const found = active.research.tasks.findIndex(task => task.agent === event.task.agent)
          if (found >= 0) active.research.tasks[found] = event.task
        }
        if (event.type === 'tool_start' || event.type === 'tool_end') {
          const found = active.tool_calls.findIndex(call => call.id === event.call.id)
          if (found < 0) active.tool_calls.push(event.call)
          else active.tool_calls[found] = event.call
        }
      })
      sessionId.value = data.session_id
      if (title.value === 'New conversation') title.value = turn.message.slice(0, 80)
      selectedPlayers.value = data.selected_players || []
      turns.value[index] = { ...turn, research_flow: data.research_flow ?? turns.value[index]?.research_flow, research: data.evidence_result?.research || turns.value[index]?.research, response: data.response, tool_calls: data.tool_calls, evidence_result: data.evidence_result, player_clarifications: data.player_clarifications, selected_players: data.selected_players, failed: data.failed }
      await refreshHistory()
    } catch (e) {
      const active = turns.value[index]!
      turns.value[index] = { ...active, research_flow: interruptFlow(active.research_flow), tool_calls: active.tool_calls.map(call => call.status === 'running' ? { ...call, status: 'failed', result: 'Live updates stopped before completion was confirmed.' } : call), failed: true, response: e instanceof Error ? e.message : 'Unable to reach the server.' }
    } finally { sending.value = false }
  }

  return { selectedPlayers, sessions, turns, sessionId, title, sending, loadingSession, loadingHistory,
    historyError, error, busy, deletingId, deleteError, refreshHistory, newChat, openSession, deleteSession, send }
}
