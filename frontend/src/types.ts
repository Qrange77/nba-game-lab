export interface ToolCall { name: string; agent?: string; node_id?: string; args: unknown; result?: unknown; id?: string; status?: 'running' | 'completed' | 'failed' | 'needs_evidence' | 'needs_revision' }
export type FlowStatus = 'queued' | 'running' | 'completed' | 'partial' | 'failed' | 'cancelled' | 'interrupted'
export interface FlowNode { id: string; label: string; role: 'lead' | 'researcher' | 'review' | 'writer'; agent: string
  depends_on: string[]; description: string; round: number; status: FlowStatus
  started_ms: number | null; ended_ms: number | null; tool_ids: string[]; summary: string }
export interface ResearchFlow { version: number; status: FlowStatus | 'clarification' | 'outside_scope'; elapsed_ms: number; peak_parallel: number; nodes: FlowNode[] }
export interface ResearchTask { agent: string; dimension: string; question: string; round: number; status: 'running' | 'completed' | 'partial' | 'unavailable' }
export interface ResearchProgress { scope: string; criteria: string; tasks: ResearchTask[]; coverage?: string; elapsed_seconds?: number; api_requests?: number; data_cutoff?: string }
export interface PlayerClarification { query: string; players: PlayerChoice[]; complete: boolean; resolved: boolean }
export interface Turn { message: string; response: string; tool_calls: ToolCall[]; research?: ResearchProgress; research_flow?: ResearchFlow | null; failed?: boolean; evidence_result?: EvidenceResult | null; activity_phase?: string; player_clarifications?: PlayerClarification[]; selected_players?: PlayerChoice[] }
export interface Session { session_id: string; title: string; updated_at: string }
export interface Conversation { session_id: string; title: string; turns: Turn[]; selected_players?: PlayerChoice[]; pending_identity?: { message: string; groups: PlayerClarification[] } | null }
export interface Metric {
  label: string; value: number | null; display_value?: string | null; unit?: string; estimated?: boolean
  unavailable_reason?: string; formula?: string; inputs?: unknown
}
export interface Panel {
  player?: string; team?: string; headshot?: string; position?: string; jersey?: string
  provisional?: boolean; metrics?: Record<string, Metric>; note?: string
}

export interface PlayerChoice {
  id: number; name: string; from_year: string | null; to_year: string | null
  active: boolean; source: string; stale: boolean
}
export interface EvidenceSource {
  provider: string; url: string; endpoint: string; fetched_at: string; stale: boolean; warning?: string
}
export interface EvidenceCard {
  evidence_id: string; title: string; player: string; value: number | null; unit: string; scope: string
  other_player?: string; other_value?: number; other_scope?: string
  games?: number | null; other_games?: number | null; covered_seasons?: string[]
  date?: string; matchup?: string; formula?: string; inputs?: unknown
  sources: EvidenceSource[]; limitations: string[]
  label?: string; award?: boolean; other_covered_seasons?: string[]
  context?: { team_id: number; team_name: string; focal_player_id: number }
  other_context?: { team_id: number; team_name: string; focal_player_id: number }
  team_games?: number | null; other_team_games?: number | null
}
export interface HonorsSummary {
  left_player: string; right_player: string; left_scope: string; right_scope: string
  rows: { metric: string; label: string; left_value: number | null; right_value: number | null; left_seasons: string[]; right_seasons: string[] }[]
  sources: EvidenceSource[]; limitations: string[]
}
export interface EvidenceResult {
  research?: ResearchProgress
  scoring?: ScoringReview
  cards: EvidenceCard[]; comparisons: StatisticalComparison[]; sources: EvidenceSource[]; limitations: string[]
  verification: { status: 'checked' | 'not_submitted' | 'partial'; checked_claims: number; note: string; attempts: { valid: boolean; errors: unknown[] }[] }
}

export interface ScoringReview {
  verdict: 'supported' | 'contradicted' | 'conditional' | 'insufficient_data' | 'comparison'
  contract: { claim: string; cutoff: number; period: string; phases: string[] }
  support_samples: {
    player_name: string; season: number; phase: string; selection: string; core: string[]
    followup?: boolean; followup_reason?: string; gap_id?: string
    rotation_records: { id: string; player_name: string; evidence_url?: string | null
      values: Record<string, { value: number | null; unit?: string }> }[]
  }[]
}

export interface StatisticalComparison {
  kind?: 'key_teammates'
  selection?: { left_focal_name: string; right_focal_name: string; scope_reason: string; teammate_reason: string }
  honors?: { metric: string; label: string; left_value: number | null; right_value: number | null; comparable: boolean }[]
  evidence_id?: string | null; left_player: string; right_player: string; left_scope: string; right_scope: string
  rows: { metric: string; label: string; group: 'basic' | 'efficiency'; left_value: number | null; right_value: number | null
    unit: string; comparable: boolean; left_complete: boolean; right_complete: boolean
    relation: 'higher' | 'lower' | 'equal' | null; difference: number | null }[]
  sources: EvidenceSource[]; limitations: string[]
}

