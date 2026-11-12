"""Evidence-linked, question-specific judgements with a separate reasoning review."""
import json
import re
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Judgement(BaseModel):
    model_config = ConfigDict(extra='forbid')
    position: Literal['left','right','close','insufficient']
    criterion: str = Field(min_length=12,max_length=500)
    reason: str = Field(min_length=15,max_length=700)
    support: list[str] = Field(default_factory=list,max_length=4)
    counterevidence: list[str] = Field(default_factory=list,max_length=4)
    counterargument: str = Field(min_length=15,max_length=600)
    tradeoff: str = Field(min_length=15,max_length=600)
    sensitivity: str = Field(min_length=15,max_length=600)

class JudgementReview(BaseModel):
    valid: bool
    issues: list[str] = Field(default_factory=list,max_length=6)

METRICS={'offense':['PTS','TS_PCT'],'playmaking':['AST36','AST_TO'],
         'defense':['STL36','BLK36','DREB36'],'team':['NET_DIFF']}

def comparisons(records,contract):
    """Compare exact scopes only; never select one of several team stints."""
    rows=[]
    for dimension in contract.impact_dimensions:
        for phase in contract.phases:
            pair=[[r for r in records if r.get('kind')=='impact_'+dimension and r['player_id']==pid and r['scope']['phase']==phase] for pid in (contract.left_player,contract.right_player)]
            for metric in METRICS[dimension]:
                complete=all(len(rs)==1 and rs[0]['values'].get(metric,{}).get('complete') for rs in pair)
                a,b=[rs[0]['values'][metric]['value'] if len(rs)==1 and metric in rs[0]['values'] else None for rs in pair]
                rows.append({'id':f'{dimension}:{phase}:{metric}','dimension':dimension,'phase':phase,'metric':metric,
                             'complete':complete,'left':a,'right':b,
                             'label':pair[0][0]['values'][metric].get('label',metric) if pair[0] else metric,
                             'unit':pair[0][0]['values'][metric].get('unit','') if pair[0] else '',
                             'samples':[{k:v['value'] for k,v in rs[0]['values'].items() if k in ('GP','ON_MIN','OFF_MIN')} if len(rs)==1 else {} for rs in pair],
                             'direction':('left' if a>b else 'right' if b>a else 'tie') if complete else 'missing',
                             'evidence_ids':[r['id'] for rs in pair for r in rs]})
    return rows

def validate(judgement,rows):
    lookup={r['id']:r for r in rows};issues=[]
    for ident in judgement.support+judgement.counterevidence:
        if ident not in lookup or not lookup[ident]['complete']:issues.append('Cited comparison is missing or incomplete: '+ident)
    if judgement.position in ('left','right'):
        if not any(lookup.get(i,{}).get('direction')==judgement.position for i in judgement.support):issues.append('A preference needs a complete comparison favoring the chosen player.')
        opposite='right' if judgement.position=='left' else 'left'
        if any(r['complete'] and r['direction']==opposite for r in rows) and not any(lookup.get(i,{}).get('direction')==opposite for i in judgement.counterevidence):issues.append('Address an actual opposing advantage, not merely a generic caveat.')
    if judgement.position=='close' and not any(r['complete'] for r in rows):issues.append('Missing data cannot establish a close contest.')
    for field in ('criterion','reason','counterargument','tradeoff','sensitivity'):
        prose=getattr(judgement,field)
        prose=prose.replace('per 36 minutes','per minute').replace('per 100 possessions','per possession')
        prose=re.sub(r'\b(?:19|20)\d{2}(?:-\d{2})?\b','season',prose)
        if re.search(r'\d',prose):issues.append('Keep prose qualitative; published numbers must come from the evidence renderer.')
    prose=' '.join(getattr(judgement,f) for f in ('criterion','reason','counterargument','tradeoff','sensitivity'))
    if re.search(r'(?i)(assist|creation).{0,65}per possession|raw assist (?:total|count|generation)|raw rebounding counts',prose):
        issues.append('Use assists per minute / per 36 minutes and defensive rebounds per minute exactly; these are not per-possession rates, raw totals or responsibilities.')
    if rows and all(r.get('dimension')=='defense' for r in rows) and judgement.position in ('left','right'):
        issues.append('Only defensive activity proxies are available. Do not rank complete individual defense from them; explain the specific measurement gap.')
    for field in ('criterion','reason','counterargument','tradeoff'):
        text=getattr(judgement,field)
        if re.search(r'(?i)spacing|gravity|rim protection|deterren|decision.making|responsibilit|off.ball|on.ball|historic|unprecedented',text) and not re.search(r'(?i)not measure|unmeasured|missing|cannot|does not|insufficient',text):
            issues.append('Do not assert unmeasured roles, gravity, spacing, deterrence or historical standing from this ledger: '+field)
    return issues

WRITER_PROMPT='''Make a question-specific basketball judgement using ONLY the supplied comparison ledger and scope.
You may prefer a player without winning every metric. Explain which relevant advantage matters more and WHY. Do not count metric wins or create an arbitrary weighted score. Respect explicit user priorities. For broad on-court questions, use a transparent observed-contribution lens: direct offensive production and recorded creation can support a provisional preference; defense and team context limit its breadth. State that assumption rather than pretending it is universal.
For playmaking, distinguish assist production from ball security; explain the tradeoff. For team dependence, answer observed on/off association, not causal dependence. For defense, activity proxies alone cannot establish complete individual defensive superiority; an insufficient judgement must still identify supported proxy advantages. Do not substitute scoring for a defense or team question.
Choose left/right for a defensible qualified preference, close only for substantively close comparable evidence, insufficient only when a specific missing input prevents the requested inference. Split indicators do NOT automatically mean close or insufficient. Never equate missing historical data with worse performance.
Provide at most two decisive reasons; cite comparison IDs in support and the strongest opposing IDs in counterevidence. Explain why the counterargument does or does not change the preference. State what changed priority or additional evidence could reverse it. Use player names, never left/right player or the opposing player. On revision, fix the stated issues without abandoning a defensible preference merely because its wording needs correction. Season labels are allowed. Use exact metric labels and units: assists per minute are not per possession, raw assists, gravity or safer decision-making. Do not infer player roles, responsibilities, spacing value, gravity, rim deterrence or historical standing from rates. Compare these two samples only; describe unmeasured dimensions only as explicit limitations or needed future evidence. No new facts, invented tracking, injuries, causal claims, or numerical prose (figures are rendered separately); the unit phrases per 36 minutes and per 100 possessions are allowed. Put comparison IDs only in the support/counterevidence arrays, never in prose. Describe observed differences, not what a player intended or prioritized. All text English. Return the schema.'''

REVIEW_PROMPT='''Independently review the proposed judgement against the original question, contract and evidence ledger. Return valid=false and concrete issues if it evades the actual question; arbitrarily weights or counts metric wins; ignores a material opposing advantage; makes ungrounded basketball/causal assertions; treats missing data as poor performance or as proof of a tie; claims complete defense from box scores; or claims insufficient evidence merely because indicators split without considering a conditional preference. Check that its stated criterion explains the choice and its reversal condition is meaningful. A qualified preference is allowed; unanimity is not required. Explicit exception: a defense-only request with activity proxies and no comprehensive defensive evidence SHOULD remain insufficient; do not force a conditional complete-defense winner in that case. Distinguish per-minute from per-possession rates and raw totals; reject inflated role/decision-making claims inferred from those metrics. Prose contains no numeric facts. This is a reasoning review, not an independent source audit.'''

def decide(investigation,rows=None):
    p=investigation.p
    if rows is None:rows=comparisons(investigation.records(),investigation.c)
    payload={'question':p.messages,'contract':investigation.c.model_dump(),'comparisons':rows,
             'coverage_gaps':[g for result in investigation.results.values() for g in result.get('gaps',[])]}
    # Only user-authored questions and clarifications define preferences.
    from backend.research.scope_review import current_question_users
    payload['question']=current_question_users(p.messages)
    payload['players']=getattr(p.research,'names',{}) if hasattr(p,'research') else {}
    question=' '.join(payload['question'])
    primary_phase='Playoffs' if re.search(r'(?i)playoff|postseason',question) and not re.search(r'(?i)regular.season',question) else ('Regular Season' if 'Regular Season' in investigation.c.phases else investigation.c.phases[0])
    investigation.priority_phase=primary_phase
    payload['priority_policy']='Use '+primary_phase+' as the primary phase for a season question unless the user explicitly prioritizes another phase. Disclose this default. Other phases are counterevidence, not an undisclosed way to change the winner. Within that phase explain the relevant production/security or volume/efficiency tradeoff.'
    base=json.dumps(payload);feedback=[];attempts=[]
    for _ in range(2):
        try:
            candidate=p.structured(WRITER_PROMPT+'\nINPUT: '+base+'\nREVISION ISSUES: '+json.dumps(feedback),Judgement,deadline=p.deadline-12)
            for field in ('criterion','reason','counterargument','tradeoff','sensitivity'):
                text=getattr(candidate,field).replace('comparison ledger','available evidence').replace('provided ledger','available evidence').replace('priority policy','stated comparison criterion')
                for side,pid in [('left',investigation.c.left_player),('right',investigation.c.right_player)]:
                    if hasattr(p,'research'):text=re.sub(r'(?i)the '+side+r' player',p.research.names[str(pid)],text)
                for row in rows:
                    if ':' in row['id']:text=text.replace(row['id'],row.get('label',row['metric']))
                setattr(candidate,field,text)
            issues=validate(candidate,rows)
            if candidate.position in ('left','right') and any(r.get('phase')==primary_phase and r['complete'] for r in rows):
                if not any(r['id'] in candidate.support and r.get('phase')==primary_phase and r['direction']==candidate.position for r in rows):issues.append('A preference must have a supporting advantage in the primary phase; do not silently replace it with postseason emphasis.')
            if not issues:
                review=p.structured(REVIEW_PROMPT+'\nINPUT: '+base+'\nPROPOSAL: '+candidate.model_dump_json(),JudgementReview,deadline=p.deadline-5)
                issues=review.issues if not review.valid else []
                if not review.valid and not issues:issues=['Reasoning review did not approve the proposal.']
            attempts.append({'priority_phase':primary_phase,'proposal':candidate.model_dump(),'issues':issues,'accepted':not issues})
            if not issues:return candidate,rows,attempts
            feedback=issues
        except Exception as exc:
            attempts.append({'accepted':False,'error':type(exc).__name__});break
    fallback=bounded_fallback(investigation,rows)
    attempts.append({'accepted':fallback is not None,'method':'bounded criterion fallback','semantic_review':False})
    return fallback,rows,attempts

def bounded_fallback(investigation,rows):
    """A disclosed, narrow criterion; failed prose review must not manufacture a tie."""
    complete=[r for r in rows if r['complete']]
    dimensions=set(r.get('dimension') for r in rows)
    if not complete or dimensions=={'defense'}:
        return Judgement(position='insufficient',criterion='Require comparable evidence that measures the requested contribution.',
            reason='Complete individual defense is not measured by defensive event rates alone.' if dimensions=={'defense'} else 'Comparable inputs needed for a preference were not returned.',
            support=[r['id'] for r in complete[:4]],counterevidence=[],
            counterargument='Available activity advantages remain useful observations, but cannot fill the missing measurement.',
            tradeoff='Missing measurement is not evidence that the players are equally strong.',
            sensitivity='Comparable evidence measuring the missing contribution could permit a preference.')
    dimension='offense' if 'offense' in dimensions else 'playmaking' if 'playmaking' in dimensions else 'team'
    metric={'offense':'TS_PCT','playmaking':'AST36','team':'NET_DIFF'}[dimension]
    from backend.research.scope_review import current_question_users
    question=' '.join(current_question_users(getattr(investigation.p,'messages',[])))
    if re.search(r'(?i)prioriti|most important|care more|focus on',question):
        if re.search(r'(?i)ball security|turnover',question):dimension,metric='playmaking','AST_TO'
        elif re.search(r'(?i)volume|points per game',question):dimension,metric='offense','PTS'
        elif re.search(r'(?i)efficien|true shooting',question):dimension,metric='offense','TS_PCT'
        elif re.search(r'(?i)assist',question):dimension,metric='playmaking','AST36'
        elif re.search(r'(?i)on[ /-]off',question):dimension,metric='team','NET_DIFF'
        else:return None
    primary=next((r for r in complete if r['dimension']==dimension and r['metric']==metric and r.get('phase')==getattr(investigation,'priority_phase',investigation.c.phases[0])),None)
    if not primary or primary['direction'] not in ('left','right'):return None
    names=[investigation.p.research.names[str(pid)] for pid in (investigation.c.left_player,investigation.c.right_player)]
    side=primary['direction'];winner=names[0 if side=='left' else 1]
    other='right' if side=='left' else 'left'
    counters=[r for r in complete if r['direction']==other][:4]
    labels={'PTS':'points per game','AST_TO':'assists per turnover','TS_PCT':'true shooting efficiency','AST36':'assists per minute','NET_DIFF':'observed on-minus-off team net rating'}
    criterion='A conditional '+primary['phase'].lower()+' preference prioritizing '+labels[metric]+'. This is a disclosed narrow lens, not a complete player ranking.'
    return Judgement(position=side,criterion=criterion,
        reason=winner+' leads the selected primary measure in the matched phase. This establishes the preference only under the stated lens.',support=[primary['id']],
        counterevidence=[r['id'] for r in counters],
        counterargument=(names[1 if side=='left' else 0]+' leads '+ '; '.join(r.get('label',r['metric'])+' in '+r['phase'] for r in counters)+'. These advantages prevent an unconditional ranking.' if counters else 'This metric does not isolate player effects or measure every relevant contribution.'),
        tradeoff='The primary criterion takes precedence for this conditional choice; the evidence does not establish that everyone should adopt that priority.',
        sensitivity='Prioritizing the opposing measures or a different phase could reverse the choice; broader measurement is needed for an overall judgement.')

def render(investigation,judgement,rows):
    names=[investigation.p.research.names[str(pid)] for pid in (investigation.c.left_player,investigation.c.right_player)]
    choice=('I lean toward '+names[0 if judgement.position=='left' else 1]) if judgement.position in ('left','right') else 'The comparable evidence is close' if judgement.position=='close' else 'The requested ranking remains unresolved'
    lookup={r['id']:r for r in rows}
    def cite(ids):return investigation.p.cite(*(e for i in ids for e in lookup[i]['evidence_ids']))
    sensitivity=judgement.sensitivity
    if judgement.position in ('left','right'):
        other=names[1 if judgement.position=='left' else 0]
        counterlabels=list(dict.fromkeys(lookup[i].get('label',lookup[i].get('metric','the cited measure'))+' in '+lookup[i].get('phase','the compared phase') for i in judgement.counterevidence))
        sensitivity=('Giving more weight to '+other+"'s advantages in "+'; '.join(counterlabels)+' could reverse this preference. ' if counterlabels else '')+'Additional comparable evidence favoring '+other+' on the requested contributions could also change this judgement.'
    prefix=['A bounded criterion fallback is used because the generated interpretation did not pass review.',''] if getattr(investigation,'judgement_attempts',[]) and investigation.judgement_attempts[-1].get('method')=='bounded criterion fallback' else []
    return ['**My judgement: '+choice+'.**','',*prefix,'**Criterion:** '+judgement.criterion,
            '','**Decisive reason:** '+judgement.reason+' '+cite(judgement.support),
            '','**Strongest counterargument:** '+judgement.counterargument+' '+cite(judgement.counterevidence),
            '','**Why this judgement:** '+judgement.tradeoff,
            '','**What could change it:** '+sensitivity]
