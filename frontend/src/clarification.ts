import type { Turn } from './types'

export interface ClarificationPrompt {
  kind: 'period' | 'influence' | 'custom'
  question: string
  players: string[]
  cutoff: number
}

export function clarificationPrompt(turn: Turn): ClarificationPrompt | null {
  if (turn.failed || turn.player_clarifications?.length || turn.research_flow?.status !== 'clarification') return null
  const call = [...turn.tool_calls].reverse().find(c => c.name === 'confirm_scoring_contract')
  if (!call) return null
  try {
    const contract = typeof call.result === 'string' ? JSON.parse(call.result) : call.result
    if (!contract || typeof contract !== 'object' || contract.action !== 'clarify') return null
    const players = (turn.selected_players || []).map(p => p.name)
    const question = turn.response
    let kind: ClarificationPrompt['kind'] = ['period', 'influence'].includes(contract.clarification_kind) ? contract.clarification_kind : 'custom'
    // Older saved turns have no UI metadata. Recognize only the unambiguous
    // career/window question; other historical clarifications remain free text.
    if (!contract.clarification_kind && /career/i.test(question) && /equal.length season windows/i.test(question)
      && /would you (?:like|prefer)/i.test(question)) kind = 'period'
    if (kind === 'period' && players.length !== 2) kind = 'custom'
    const cutoff = Number.isInteger(contract.cutoff) && contract.cutoff >= 1984 ? contract.cutoff : 1984
    return { kind, question, players, cutoff }
  } catch { return null }
}

export function seasonLabel(start: number): string {
  return `${start}-${String((start + 1) % 100).padStart(2, '0')}`
}

export function windowReply(players: string[], years: string[], cutoff: number): { message: string; error: string } {
  if (players.length !== 2 || years.length !== 4 || years.some(y => !/^\d{4}$/.test(y)))
    return { message: '', error: 'Enter all four season start years, such as 1990 for 1990-91.' }
  const [a, b, c, d] = years.map(Number) as [number, number, number, number]
  if ([a, b, c, d].some(y => y < 1984 || y > cutoff))
    return { message: '', error: `Choose completed seasons from 1984-85 through ${seasonLabel(cutoff)}.` }
  if (a > b || c > d) return { message: '', error: 'Each end season must be the same as or later than its start season.' }
  if (b - a !== d - c) return { message: '', error: 'Use the same number of seasons for both players.' }
  return { message: `Use ${players[0]} in ${seasonLabel(a)} through ${seasonLabel(b)}, and ${players[1]} in ${seasonLabel(c)} through ${seasonLabel(d)}.`, error: '' }
}
