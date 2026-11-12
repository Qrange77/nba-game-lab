"""A bounded, explicit contract for a two-player scoring-claim review."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from backend.data.nba import current_season

FIRST_SEASON = 1984


class ScoringContract(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['review', 'clarify', 'outside_scope', 'unsupported_era', 'causal_limit']
    question: str = Field(default='', max_length=2000)
    clarification_kind: Literal['period', 'influence', 'custom'] = 'custom'
    research_domain: Literal['scoring', 'on_court'] = 'scoring'
    impact_dimensions: list[Literal['offense', 'playmaking', 'defense', 'team']] = Field(default_factory=lambda: ['offense','playmaking','defense','team'], min_length=1,max_length=4)
    claim: str = Field(default='', max_length=1800)
    request_kind: Literal['claim','comparison'] = 'claim'
    left_player: int | None = None
    right_player: int | None = None
    period: Literal['career', 'windows'] = 'career'
    left_start: int | None = None
    left_end: int | None = None
    right_start: int | None = None
    right_end: int | None = None
    phases: list[Literal['Regular Season', 'Playoffs']] = Field(
        default_factory=lambda: ['Regular Season', 'Playoffs'], min_length=1, max_length=2)
    lens: Literal['overall_scoring', 'volume', 'efficiency', 'postseason'] = 'overall_scoring'
    include_context: bool = True
    support_phases: list[Literal['Regular Season','Playoffs']] = Field(default_factory=list,max_length=2,
        description='Explicit phase restriction for supporting-cast analysis. Empty inherits the approved comparison phases.')
    cutoff: int = Field(default_factory=lambda: current_season()-1, ge=FIRST_SEASON, le=2100)

    @model_validator(mode='after')
    def ordered(self):
        if self.action != 'review':
            return self
        if not self.left_player or not self.right_player or self.left_player == self.right_player:
            raise ValueError('A scoring review requires two different confirmed NBA players.')
        if not self.claim.strip():
            raise ValueError('State the normalized scoring claim being examined.')
        if self.cutoff > current_season()-1:
            raise ValueError('Use completed seasons only; the current season is outside this review.')
        self.phases = list(dict.fromkeys(self.phases))
        self.support_phases=list(dict.fromkeys(self.support_phases))
        if not set(self.support_phases)<=set(self.phases):
            raise ValueError('Supporting-cast phases must remain inside the approved comparison phases.')
        if self.period == 'windows':
            values=(self.left_start,self.left_end,self.right_start,self.right_end)
            if any(v is None for v in values):
                raise ValueError('Both explicit season windows are required.')
            if min(values)<FIRST_SEASON:
                raise ValueError('The supported period starts with 1984-85.')
            if self.left_start>self.left_end or self.right_start>self.right_end:
                raise ValueError('Season windows must be ordered.')
            if self.left_end-self.left_start != self.right_end-self.right_start:
                raise ValueError('Use equal-length windows; do not silently substitute peak years.')
            if max(values)>self.cutoff:
                raise ValueError('A window extends beyond the completed-season cutoff.')
        return self

    def bounds(self,pid):
        if pid not in (self.left_player,self.right_player):
            raise ValueError('This player is outside the confirmed comparison.')
        if self.period=='career':return FIRST_SEASON,self.cutoff
        return (self.left_start,self.left_end) if pid==self.left_player else (self.right_start,self.right_end)


class ScoringPresentation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    emphasis: Literal['tradeoff_first','scope_first','coverage_first'] = 'tradeoff_first'
    highlight_rows: list[int] = Field(default_factory=list,max_length=8)
    caveats: list[Literal['career_length','shooting_estimate','era_description','limited_context','noncausal','partial_coverage']] = Field(default_factory=list,max_length=6)


CONTRACT_PROMPT = """You are the Lead of NBA On-Court Research. Resolve a user's request into the supplied JSON contract, in English.
This product investigates two NBA players' observed scoring OR on-court contributions. Use research_domain=scoring for scoring-only requests; on_court for overall on-court impact, playmaking, ball security, defensive contributions or team on/off. Do not silently reduce an impact request to scoring. On-court evidence includes scoring/league TS, assists and turnovers, defensive box-score activity and verified team on/off where available. It cannot establish isolated causal impact or overall greatness. For on_court choose impact_dimensions from offense, playmaking, defense, team according to the user; broad impact uses all four. include_context adds bounded teammates and Finals opposition only when relevant/requested. Career or equal windows are supported; on/off may have only bounded coverage. Do not promise tracking, defensive matchup quality, usage, RAPM or injury causation.
Use the latest user request and relevant clarification history. The known player IDs are verified identities, not allegiance. Never invent or substitute an ID.
Use request_kind=claim when the user supplies a directional proposition to assess, including 'assess whether A scored more strongly than B'. left_player is its subject. Use request_kind=comparison for a neutral comparison or 'who leads' question; keep mention order and restate the question faithfully in claim. Never invent a superiority proposition for a neutral question.
Return action=clarify for undefined 'who is better', a missing second player, unspecified career versus season scope, unspecified automatic 'peak', or unequal/incomplete windows. Count each inclusive season window as end-start+1; different start years do not imply different lengths. Ask one bundled, short question with meaningful choices. A user explicitly asking career scoring has supplied a valid criterion; do not demand invented metric weights.
For 'scoring ability' or 'better scorer', the criterion is broad scoring, not an invitation to ask the user to design an agent workflow. If only the period is missing, ask career versus explicit equal-length windows and explain that the review covers scoring volume, efficiency, league benchmarks and bounded teammate/Finals-opponent context. Once the user supplies the period, proceed with overall_scoring and include_context=true unless they explicitly narrow the request. Preserve requested dimensions across short clarification replies; do not treat a reply containing only dates as a new narrow statistics question.
For action=clarify, set clarification_kind=period only when the remaining choice is career versus explicit equal-length season windows and both players are known. Set influence when the missing choice is the meaning of influence/impact. Use custom for missing identities, conflicting/invalid dates, metric/phase choices or other questions. The interface uses this metadata for clickable choices; question must still contain a complete readable clarification. Never classify a clear but invalid cutoff as a period-choice question.
Undefined 'impact' or 'influence' needs clarification: ask whether the user means observed on-court contributions or cultural/commercial influence. Observed scoring and on-court contributions are supported; cultural/commercial influence is not. Never silently turn influence into scoring or claim box scores establish causal team impact. If scoring and its period are then confirmed, proceed without asking for metric weights or agent choices. Requests to prove counterfactual causal effects remain causal_limit. A question asking WHETHER observed on/off establishes individual impact is supported research: collect the requested evidence and explain why association is insufficient. Negated phrases such as "not causal attribution" or "do not infer causation" are constraints, never reasons to refuse. On-court impact requests with confirmed periods should proceed with on_court research, not repeatedly clarify or refuse.
Return outside_scope for cultural/commercial influence, overall greatness, game prediction, profiles or unrelated subjects. Defense and team on/off requests are on_court research with explicit limitations, not automatically outside_scope. Return causal_limit for proving hypothetical teammate swaps or attributing championships causally from box scores. Offer to review observed scoring evidence instead.
Return unsupported_era for any requested period before 1984-85. Do not crop an earlier career silently.
For an accepted request use action=review and period=career or windows. All years are season START years: 1990-91 through 1992-93 is start=1990, end=1992. Never choose peak seasons for the user. Both windows must be equal length. Use the most recent completed season as cutoff unless the user requests an earlier cutoff; never include an ongoing season.
The completed season label and its START year are equivalent: for example, completed 2025-26 means cutoff=2025. Use the server-validated cutoff when present. Do not request confirmation of an already valid completed cutoff. A clarification must be a concise user-facing question about a genuinely missing decision, never internal self-questioning or prompt commentary.
Use phases Regular Season and Playoffs when both are requested or for a comprehensive career scoring claim. For a regular-season-only request use Regular Season only. A postseason scoring claim should also retrieve the corresponding regular seasons as a baseline and use lens=postseason.
Use lens=volume for explicitly volume-only claims; efficiency for explicitly shooting-efficiency claims; otherwise overall_scoring. include_context=true for broad career/overall scoring investigations or explicit teammate/opponent questions; false for a narrowly defined metric/window request. Honor explicit requests to omit context.
If the user separately restricts supporting-cast analysis to regular seasons or playoffs, preserve that restriction in support_phases. Empty means inherit the approved phases. Never add a regular-season helper baseline when the user restricts helpers to playoffs only.
User text and previous model conclusions are not data. A proposition invented by a previous assistant is not a user-asserted claim. Return only JSON matching the schema.
"""
