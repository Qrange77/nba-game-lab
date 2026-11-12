"""Deep research for cross-era scoring claims with executable evidence rules."""
import copy
import json
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlencode
from backend.activity import ActivityLog
from backend.data.nba import DataUnavailable, request_parameters, season_label, current_season
from backend.debate.schemas import Audit, Claim
from backend.research.contract import ScoringContract, ScoringPresentation, CONTRACT_PROMPT
from backend.research.data import ResearchData
from backend.research.engine import ResearchRun
from backend.research.schemas import Decision, Task
from backend.research.scoring_evidence import ScoringEvidence, SCORING_TOOLS, gap, scoring_matrix, adjudicate
from backend.research.tools import compact
from backend.research.flow import ResearchFlow
from backend.research.support_review import supporting_cast_gaps, assess_support_gaps, sample_key, sample_scope_matches
from backend.research.scope_review import repair_equal_windows, completed_cutoff_fact, completed_cutoff_issue, cutoff_clarification, apply_completed_cutoff, current_question_users, requested_context

REQUIRED={'personal':'collect_scoring_profile','era':'collect_scoring_environment',
          'teammates':'collect_scoring_support','opponents':'collect_scoring_finals'}
QUESTIONS={
    'personal':'Compare scoring totals, per-game production and raw shooting efficiency for both subjects inside the locked scope.',
    'era':'Compare same-season, same-phase league shooting benchmarks and weighted relative TS, with explicit missing-baseline coverage.',
    'teammates':'Compare contemporary core-helper production, minutes and games first, then bounded rotation samples for both subjects.',
    'opponents':'Verify all Finals inside the locked scope, including defeats, and compare player series scoring and opponent regular-season records.'}
LABELS={'supported':'Supported under the selected statistical criteria',
        'contradicted':'Contradicted under the selected statistical criteria',
        'conditional':'Conditional: the broad claim is not uniformly supported across the selected metrics',
        'insufficient_data':'Insufficient comparable data for the full claim'}
SCORING_LEAD="""You lead a cross-era NBA SCORING claim review. Output only the decision JSON schema.
The locked contract defines the two players, periods, phases and cutoff. Do not broaden it to overall greatness, defense, games, prediction or causal championship credit.
Initial action must be research. Fan out in ONE response to one task per required dimension: personal (volume, efficiency and postseason changes), era (contemporaneous shooting benchmarks), and, when required, teammates and opponents. All run in parallel in fresh contexts. Explain the relevant investigative question rather than demanding a predetermined winner. Both players must receive comparable coverage.
Available evidence is points, minutes, games, shooting attempts/percentages, weighted relative TS, bounded teammate scoring/minutes/games, Finals scoring and opponent regular-season records. Do not request usage, spacing, tracking, defensive ratings or defensive schemes. Do not ask how teammates caused or impacted scoring. Context tasks describe observed production and limitations only.
In a review, inspect the actual findings and CONTENT CHECKS as well as collector completion. A completed collector may still leave an unanswered sample-adequacy question: a helper selected by PPG may have very sparse appearances, the phase may not match the question, or required helper metrics may be missing. Use the supplied evidence and approved matched targets. For a content follow-up copy its exact gap_id into the teammate task; inspect_supporting_cast retrieves the missing matched phase or alternate source. State what evidence is missing and what the investigation can resolve. Preserve original observations. Do not retry merely because a conclusion is unwelcome. Do not claim a new phase establishes playoff availability, injury causes or innate support quality.
A collection omission remains retryable. A source exhausted after its alternative failed is unavailable; disclose it. Reuse existing scoped evidence when it already answers the question. You may finish when no actionable required gap remains or the budget cannot support another attempt. Do not repeat completed collectors; a concrete content gap may revisit the teammate dimension using its targeted investigation. Never interpolate missing seasons.
Use the exact contract scope and scoring criteria in every research decision. Only personal, era, teammates and opponents dimensions are supported. A follow-up may contain one task. Return no hidden reasoning.
If a CONTENT CHECK is retryable, return action=research with a teammate task and that exact gap_id, even when the first collection completed successfully. Collector success does not establish content sufficiency. Treat researcher notes as working hypotheses; use the verified matrix and scoped source evidence as facts.
"""
SCORING_RESEARCHER="""You are an independent NBA scoring researcher. Use English only.
Your task, locked comparison contract and verified identities are supplied. You have a fresh conversation and cannot access another researcher's notes. Start by invoking the collector assigned to your task. Collectors enforce the same players, periods, phases and cutoff for all researchers.
Inspect coverage, counterevidence and scope. If an argument is invalid, repair it once; collectors take no arguments. Do not call a completed collector repeatedly. Do not replace missing evidence from memory. Do not infer injuries, defensive physicality, innate ability, causation or hypothetical teammate swaps from statistics.
Finish in at most eight concise bullets stating relevant findings and exact coverage limitations, with evidence IDs where available. These are research notes, not a final overall verdict. The server independently checks required collection and every published statistical comparison.
"""
SCORING_WRITER="""You are the Writer for a cross-era NBA scoring-claim audit.
The verified comparison matrix, fixed statistical adjudication, scope and coverage are supplied. Choose the report emphasis, useful matrix row indices to highlight and applicable caveats using the schema. Highlight at least one counterexample when metric directions differ. Do not select an unavailable metric as a decisive result.
Choose at most three answer-bearing highlights. For volume prefer total points and PPG; for efficiency prefer raw and relative TS; for postseason prefer playoff PPG and TS rather than regular-season totals. Distinguish a higher playoff level from a larger regular-season-to-playoff change. Prioritize evidence that answers the question over repeated methodological warnings. A neutral comparison asks who leads; it does not assert a claim to contradict.
The matrix supplied here is already restricted to the requested statistical lens. Choose highlights only from these rows; omitted metrics are not missing evidence. The server renders your selected structure using verified fact templates and exact evidence references, so no free-form factual prose or new numbers are allowed. A conditional statistical verdict is not an overall-player ranking. Relative TS is descriptive and does not isolate a causal era effect. Team context cannot prove why a player scored or won.
Return JSON only. Choose coverage_first if key evidence is missing. The output includes the supplied matrix and relevant caveats, even when not highlighted.
"""


class ScoringRun(ResearchRun):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.data=ResearchData(self.deadline-40,cache_path=getattr(self.research.data,'path',None),max_requests=160)
        self.contract=None
        self.results={}
        self.published_claims=[]
        self.flow=ResearchFlow(self.emit)
        self.flow_frontier=['lead']
        self.flow_agents={}
        self.lead_log.node_id='lead'
        self.content_checks=[]
        self.content_results={}
        self.content_attempts={}

    def record_lead(self,name,result):
        self.lead_log.start(name,{})
        self.lead_log.append({'name':name,'args':{},'result':json.dumps(result)})
        self.log.extend(self.lead_log[-1:])

    def resolve_contract(self):
        users=current_question_users(self.messages)
        latest=users[-1] if users else ''
        if re.search(r'(?i)(swap.{0,40}teammate|teammate.{0,40}swap|prove.{0,80}championship|would.{0,50}championship)',latest):
            return ScoringContract(action='causal_limit')
        if re.search(r'\b(?:19[4-7]\d|198[0-3])(?:-\d{2})?\b',latest):
            return ScoringContract(action='unsupported_era')
        if re.search(r'(?i)photo|profile|predict.{0,20}game',latest) and not re.search(r'(?i)scor|shoot|efficien',latest):
            return ScoringContract(action='outside_scope')
        if len(users)==1 and re.search(r'(?i)who.{0,20}(better|best|stronger)',latest) and not re.search(r'(?i)scor|shoot|efficien|points|defen|playmak|on.court|on.off',latest):
            return ScoringContract(action='clarify')
        if len(users)==1 and re.search(r'(?i)defen|playmak|on.court|on.off',latest) and not re.search(r'(?i)\b(?:19|20)\d{2}\b|career',latest):
            return ScoringContract(action='clarify',research_domain='on_court',clarification_kind='period',question='Choose complete careers or equal-length season windows for the on-court comparison.')
        cutoff_issue=completed_cutoff_issue(self.messages)
        if cutoff_issue:
            return ScoringContract(action='clarify',question=cutoff_issue)
        cutoff_fact=completed_cutoff_fact(self.messages)
        prompt=CONTRACT_PROMPT+'\nLATEST COMPLETED SEASON: '+season_label(current_season()-1)+\
            ' (season START year '+str(current_season()-1)+'). The two labels denote the same season.'+\
            '\nSERVER-VALIDATED USER CUTOFF: '+json.dumps(cutoff_fact)+\
            '\nUse that explicit cutoff when supplied, otherwise the latest completed season.\nCONTEXT:\n'+self.context()
        try:
            contract=self.structured(prompt,ScoringContract,deadline=self.deadline-50)
            if contract.action=='clarify' and re.search(r'(?i)on(?:[ -]the)?[ -]court|team.{0,30}(?:depend|relied|rely|need)|help(?:ed)?.{0,20}teammate',latest) and re.search(r'(?i)cultural|commercial|meaning of|mean.*impact|refer to|something else',contract.question):
                contract=self.structured(prompt+'\nSCOPE CORRECTION: The user explicitly asked about on-court performance, helping teammates, or team dependence. In this basketball comparison those refer to observed contributions or team on/off association, not cultural/commercial influence. Do not ask the user to reconfirm that meaning. Preserve supplied dates and players and proceed when scope is complete.',ScoringContract,deadline=self.deadline-50)
            if contract.action=='causal_limit' and re.search(r'(?i)on[ /-]off',latest):
                contract=self.structured(prompt+'\nReview scope: an on/off question asking whether association establishes impact is a supported descriptive investigation, not a demand to fabricate causation. Preserve the requested scope, return on_court review when dates and players are supplied, and explain causal limits in the report.',ScoringContract,deadline=self.deadline-50)
            if cutoff_clarification(contract,cutoff_fact):
                # Resolve notation internally once; preserve any real remaining ambiguity.
                contract=self.structured(prompt+'\nSCOPE VALIDATION: The explicit user cutoff is valid and completed. '
                    'The season label and its start year agree. Resolve the original request again. '
                    'Do not ask the user to confirm this notation or expose self-questioning. '
                    'Ask clarification only for a different, genuinely missing scope decision.',
                    ScoringContract,deadline=self.deadline-50)
                self.record_lead('recheck_scoring_scope',{'reason':'Validated the explicit completed-season cutoff internally.',
                    'cutoff':cutoff_fact,'action':contract.action})
            corrected=apply_completed_cutoff(contract,cutoff_fact)
            if corrected is not contract:
                self.record_lead('recheck_scoring_scope',{'reason':'Preserved the explicit user cutoff instead of the model default.',
                    'cutoff':cutoff_fact,'action':corrected.action})
                contract=corrected
        except ValueError:
            return ScoringContract(action='clarify',question='Name two players and choose complete careers or two equal-length season windows. Should the claim concern scoring volume, shooting efficiency, or both?')
        corrected=repair_equal_windows(contract,self.messages,self.research.names)
        if corrected is not contract:
            self.record_lead('repair_scoring_scope',{'reason':'Both explicit inclusive season windows have equal length.',
                'original_action':contract.action,'action':'review',
                'seasons_per_window':corrected.left_end-corrected.left_start+1})
            contract=corrected
        if contract.action=='review':
            mixed_lens=bool(re.search(r'(?i)(volume|points.per.game|accumulat).{0,120}(efficien|true.shooting)|(efficien|true.shooting).{0,120}(volume|points.per.game|accumulat)',latest))
            exclusive_lens=bool(re.search(r'(?i)(volume|efficiency)[ -]only|only (?:scoring )?(?:volume|efficiency)|(?:ignore|exclude|without|not) (?:shooting )?(?:efficiency|volume)',latest))
            if contract.lens in ('volume','efficiency') and mixed_lens and not exclusive_lens:
                contract.lens='overall_scoring'
            if contract.research_domain=='scoring':contract.include_context=requested_context(users,contract)
            else:
                contract.include_context=bool(re.search(r'(?i)teammate|supporting|rotation|opponent|finals|helper', ' '.join(users)))
                impact_text=' '.join(users)
                if re.search(r'(?i)help(?:ed)?.{0,20}teammate|mak.{0,20}teammate.{0,20}better',impact_text) and not re.search(r'(?i)scoring|defens|overall',impact_text):
                    contract.impact_dimensions=['playmaking','team']
                    contract.include_context=False
                if re.search(r'(?i)team.{0,30}(?:depend|relied|rely|need)',impact_text):
                    contract.impact_dimensions=['team']
                if re.search(r'(?i)on[ /-]off',impact_text):
                    contract.impact_dimensions=list(dict.fromkeys(contract.impact_dimensions+['team']))
                    if not re.search(r'(?i)overall|on.court (?:contribut|impact)|offense|defensive evidence|scoring|playmak|ball security|defensive (?:contribut|box|activity)|offensive (?:contribut|production)',impact_text):
                        contract.impact_dimensions=['team']
            if not {contract.left_player,contract.right_player}<=set(map(int,self.research.names)):
                return ScoringContract(action='clarify',question='Please confirm the two players for this scoring comparison before I retrieve their statistics.')
            if contract.period=='career':
                for pid in (contract.left_player,contract.right_player):
                    try:
                        entry=self.data.fetch('career',player_id=pid,per_mode36='Totals',league_id_nullable='00')
                        years=[int(r['SEASON_ID'][:4]) for r in entry['data'].get('SeasonTotalsRegularSeason',[])
                               if r.get('LEAGUE_ID','00')=='00' and r.get('GP')]
                        if years and min(years)<1984:
                            return ScoringContract(action='unsupported_era',question='This career starts before the supported 1984-85 boundary. Choose an explicit equal-length window starting in 1984-85 or later; I will not silently truncate the career.')
                    except DataUnavailable:
                        pass
        return contract

    def required_dimensions(self):
        return ['personal','era']+(['teammates','opponents'] if self.contract.include_context else [])

    def fan_out(self,decision,round_number):
        decision.tasks=decision.tasks[:max(0,8-len(self.tasks))]
        ids=[]
        labels={'personal':'Scoring evidence','era':'Era benchmarks','teammates':'Supporting cast','opponents':'Finals opponents'}
        for offset,task in enumerate(decision.tasks,1):
            number=len(self.tasks)+offset
            agent=f'Researcher {number} · {task.dimension}'
            ident=f'researcher-{number}'
            self.flow_agents[agent]=ident
            if task.gap_id:self.content_attempts[task.gap_id]=self.content_attempts.get(task.gap_id,0)+1
            self.flow.add(ident,'Helper follow-up' if task.gap_id else labels[task.dimension],'researcher',agent,self.flow_frontier,
                task.question,round_number,queued=True)
            ids.append(ident)
        result=super().fan_out(decision,round_number)
        if ids:self.flow_frontier=ids
        return result

    def decision(self,review=False):
        required=self.required_dimensions()
        if review:
            self.refresh_content_checks()
            self.record_lead('review_content_evidence',{'status':'needs_followup' if any(c['status']=='retryable' for c in self.content_checks) else 'reviewed',
                'checks':self.content_checks})
        coverage=self.coverage() if review else []
        prompt=SCORING_LEAD+'\nLOCKED CONTRACT:\n'+self.contract.model_dump_json()
        prompt+='\nREQUIRED DIMENSIONS:\n'+json.dumps(required)
        if review:
            prompt+='\nCOVERAGE:\n'+json.dumps(coverage)+'\nFINDINGS:\n'+json.dumps([{k:v for k,v in f.items() if k!='findings'} for f in self.findings])
            prompt+='\nVERIFIED COMPARISON MATRIX:\n'+json.dumps(scoring_matrix(self.current_evidence(),self.contract))
            prompt+='\nCONTENT CHECKS:\n'+json.dumps(self.content_checks)
            proof={ident for item in self.content_checks for ident in item['evidence_ids']}
            prompt+='\nSCOPED SUPPORT EVIDENCE:\n'+json.dumps([compact(self.research.evidence[i]) for i in sorted(proof) if i in self.research.evidence])
        for attempt in range(2):
            try:
                choice=self.structured(prompt,Decision,deadline=self.deadline-40)
            except ValueError:
                prompt+='\nREPAIR: return a valid decision with the required dimensions, explicit scope and criteria.'
                continue
            dimensions=[t.dimension for t in choice.tasks]
            valid=(choice.action=='finish' if review else False) or (choice.action=='research' and all(d in required for d in dimensions)
                and (review or (set(dimensions)==set(required) and len(dimensions)==len(required) and not any(t.gap_id for t in choice.tasks))))
            if valid:break
            prompt+='\nREPAIR: initial research must include every required dimension exactly once; review may finish or research only required gaps.'
        else:
            missing=[c for c in coverage if c['status']=='retryable'] if review else [{'dimension':d} for d in required]
            self.record_lead('repair_research_plan',{'reason':'The proposed plan violated required task coverage; repaired to the approved contract.','dimensions':missing})
            choice=Decision(action='research' if missing else 'finish',
                scope=self.describe_scope(),criteria='Scoring volume and efficiency within the approved contract.',
                tasks=[self.gap_task(c) for c in missing])
        # Planning prose cannot expand a bounded collector's available evidence.
        # Keep useful model questions; repair unsupported promises visibly.
        repaired=[]
        for task in choice.tasks:
            unsupported=bool(re.search(r'(?i)defen|per.minute|per.possession|usage|spacing|tracking|physicality',task.question))
            unsupported |= task.dimension=='era' and bool(re.search(r'(?i)pace|offensive.rating',task.question))
            unsupported |= task.dimension in ('personal','era') and self.contract.phases==['Regular Season'] and bool(re.search(r'(?i)playoff|postseason|finals',task.question))
            if unsupported:
                task.question=QUESTIONS[task.dimension]
                repaired.append(task.dimension)
        if repaired:self.record_lead('repair_research_plan',{'reason':'Investigation wording was constrained to supported metrics and approved phases.','dimensions':repaired})
        if review and choice.action=='research':
            retryable={(c['dimension'],c.get('gap_id','')) for c in coverage if c['status']=='retryable'}
            unique={(t.dimension,t.gap_id):t for t in choice.tasks if (t.dimension,t.gap_id) in retryable}
            if len(unique)!=len(choice.tasks):
                self.record_lead('repair_research_plan',{'reason':'Follow-up may investigate only retryable required gaps.','dimensions':list(unique)})
            choice.tasks=list(unique.values())
            if not choice.tasks:choice=Decision(action='finish')
        choice.scope=self.describe_scope()
        choice.criteria='Scoring volume, raw and contemporaneous relative efficiency; bounded context; no overall score.'
        if review and choice.action=='finish':
            retryable=[c for c in coverage if c['status']=='retryable']
            if retryable and len(self.tasks)<8 and time.monotonic()<self.deadline-65:
                self.record_lead('finish_blocked',{'reason':'Required evidence has retryable gaps.','gaps':retryable})
                choice=Decision(action='research',scope=self.describe_scope(),criteria=choice.criteria,
                    tasks=[self.gap_task(c) for c in retryable])
        for task in choice.tasks:
            if task.gap_id:
                check=next(c for c in self.content_checks if c['id']==task.gap_id)
                task.question='Evidence-driven follow-up: '+check['reason']+' '+check['question']
        self.record_lead('review_research' if review else 'plan_research',choice.model_dump())
        return choice

    def gap_task(self,cell):
        return Task(dimension=cell['dimension'],gap_id=cell.get('gap_id',''),
            question=cell.get('reason') or QUESTIONS[cell['dimension']])

    def refresh_content_checks(self):
        samples=self.results.get('collect_scoring_support',{}).get('samples',[])
        added=[s for result in self.content_results.values() for s in result.get('samples',[])]
        checks=supporting_cast_gaps(self.contract,samples,self.current_evidence())
        self.content_checks=assess_support_gaps(checks,self.current_evidence(),samples+added,self.content_results,self.content_attempts)

    def worker(self,task,agent,scope):
        ident=self.flow_agents.get(agent)
        if ident:self.flow.start(ident)
        deadline=min(self.deadline-45,time.monotonic()+125)
        inquiry=next((c for c in self.content_checks if c['id']==task.gap_id),None) if task.gap_id else None
        child=ScoringEvidence(self.contract,support_targets=copy.deepcopy(inquiry['targets']) if inquiry else None,
            data=self.data,players=[{'id':int(k),'name':v} for k,v in self.research.names.items()],catalog=self.research.catalog)
        collector='inspect_supporting_cast' if inquiry else REQUIRED[task.dimension]
        tools=[t for t in SCORING_TOOLS if t['function']['name']==collector]
        log=ActivityLog(self.emit,agent=agent,node_id=ident)
        messages=[{'role':'system','content':SCORING_RESEARCHER},
            {'role':'user','content':json.dumps({'task':task.model_dump(),'contract':self.contract.model_dump(),
                'confirmed_players':self.research.names,'required_collector':collector,'evidence_gap':inquiry,
                'original_evidence':[compact(self.research.evidence[i]) for i in inquiry['evidence_ids'] if i in self.research.evidence] if inquiry else []})}]
        notes=''
        try:
            for _ in range(4):
                reply=self.call(messages,deadline=deadline,tools=tools,max_tokens=1800,
                    tool_choice={'type':'function','function':{'name':collector}} if _==0 else 'auto')
                messages.append(reply.model_dump())
                if not reply.tool_calls:
                    notes=reply.content or '';break
                for call in reply.tool_calls:
                    args={}
                    try:
                        args=json.loads(call.function.arguments)
                        if not isinstance(args,dict):raise ValueError('Tool arguments must be an object.')
                        log.start(call.function.name,args)
                        result=child.dispatch(call.function.name,args) if call.function.name==collector else json.dumps({'error':'This collector is not assigned to the task.'})
                    except Exception as exc:result=json.dumps({'error':type(exc).__name__+': '+str(exc)[:300]})
                    log.append({'name':call.function.name,'args':args,'result':result})
                    messages.append({'role':'tool','tool_call_id':call.id,'content':result})
        except Exception as exc:
            notes='Research was interrupted by '+type(exc).__name__+'. Collected evidence remains available.'
            log.fail_pending('The task stopped before completion.')
        result=child.collector_results.get(collector)
        if result is None:notes='No verified collection completed. Model-written assertions were not accepted as research findings.'
        else:
            notes='\n'.join(line for line in notes.splitlines() if not re.search(r'(?i)injur|shoulder|due to|caused|driven by|durable|superior|inferior|unmatched|unprecedented',line))
        status='completed' if result and not result.get('gaps') else 'partial'
        issues=result.get('gaps',[]) if result else [gap(task.dimension,collector,'Required collector was not completed.','retryable')]
        if result is not None:
            with self.lock:
                if inquiry:
                    for sample in result.get('samples',[]):sample['followup_reason']=inquiry['reason'];sample['gap_id']=inquiry['id']
                    self.content_results[inquiry['id']]=result
                else:self.results[collector]=result
        if ident:self.flow.finish(ident,status,
            ('Matched supporting-cast evidence collected; original samples retained.' if inquiry else 'Required collection completed.') if status=='completed' else 'Evidence gaps remain; inspect the collector output and subsequent Lead review.',
            [call['id'] for call in log])
        return {'agent':agent,'dimension':task.dimension,'task':task.question,'status':status,
            'notes_status':'Working notes only; Lead content checks and final report facts use verified scoped evidence.',
            'findings':notes[:5000],'gaps':issues,'evidence_ids':sorted(child.used_evidence)},child,log

    def coverage(self):
        cells=[]
        for dimension in self.required_dimensions():
            result=self.results.get(REQUIRED[dimension])
            if result is None:
                cells.append({'dimension':dimension,'status':'retryable','reason':'The assigned collector has not produced verified evidence.'})
            elif result.get('gaps'):
                cells.append({'dimension':dimension,'status':'unavailable','reason':'Specific source/participation gaps remain after available API alternatives.','gaps':result['gaps']})
            else:cells.append({'dimension':dimension,'status':'completed','reason':'Required collection completed; bounded sample limitations still apply.'})
        cells += [{'dimension':'teammates','gap_id':c['id'],'status':c['status'],
            'reason':c['reason']+' '+c.get('resolution',''),'evidence_ids':c['evidence_ids']} for c in self.content_checks]
        return cells

    def describe_scope(self):
        c=self.contract
        if c.period=='career':period='Recorded careers through '+season_label(c.cutoff)
        else:period=f"{season_label(c.left_start)}–{season_label(c.left_end)} versus {season_label(c.right_start)}–{season_label(c.right_end)}"
        return period+'; '+', '.join(c.phases)

    def current_evidence(self):
        return {key:self.research.evidence[key] for key in self.research.used_evidence}

    def cite(self,*ids):
        urls=[]
        session=getattr(self.research,'session_id',None)
        for ident in dict.fromkeys(i for i in ids if i):
            record=self.research.evidence.get(ident)
            if not record:continue
            if session:
                record_urls=[f'/sessions/{session}/evidence/{ident}']
            else:
                record_urls=[]
                for source in record.get('sources',[]):
                    url=source.get('endpoint') or source.get('url')
                    if not url:continue
                    params=source.get('request_parameters') or request_parameters(source)
                    if params:url+='?'+urlencode(params)
                    record_urls.append(url)
            for url in record_urls:
                if url not in urls:urls.append(url)
        return ' '.join(f'[Evidence]({url})' for url in urls)

    def value(self,ident,key):
        record=self.research.evidence[ident]
        item=record.get('values',{}).get(key,{})
        value=item.get('value')
        if value is None:return 'Unavailable'
        self.published_claims.append(Claim(evidence_id=ident,metric=key,player_id=record['player_id'],scope=record['scope'],value=value))
        return f'{value:,.2f}'.rstrip('0').rstrip('.')

    def report_rows(self,matrix):
        if self.contract.lens=='volume':return [r for r in matrix if r['metric']=='PTS']
        if self.contract.lens=='efficiency':return [r for r in matrix if r['metric'] in ('TS_PCT','WEIGHTED_RTS')]
        return matrix

    def scoring_position(self,matrix):
        """An explicit, disclosed rate/efficiency judgement, never an overall rank."""
        c=self.contract
        if getattr(self,'reviewed_scoring_position',None):return self.reviewed_scoring_position
        if c.lens!='overall_scoring':return []
        metrics=['PTS','TS_PCT']
        if any(r['metric']=='WEIGHTED_RTS' for r in matrix):metrics.append('WEIGHTED_RTS')
        primary=[r for r in matrix if r['phase'] in c.phases and r['basis']=='per_game' and r['metric'] in metrics]
        expected={(phase,metric) for phase in c.phases for metric in metrics}
        if {(r['phase'],r['metric']) for r in primary}!=expected or any(not r['complete'] for r in primary):
            return ['**Scoring verdict: there is not enough comparable rate-and-efficiency evidence to name a winner.**']
        directions={r['direction'] for r in primary}-{'tie'}
        rule='This judgement prioritizes points per game and shooting efficiency over accumulated points; teammate and opponent records provide context, not a causal adjustment.'
        if len(directions)==1 and directions<={'left','right'}:
            direction=next(iter(directions))
            winner=self.research.names[str(c.left_player if direction=='left' else c.right_player)]
            other=self.research.names[str(c.right_player if direction=='left' else c.left_player)]
            lines=['**Scoring verdict: I favor '+winner+' in the selected sample.**',
                winner+' has the stronger rate-and-efficiency case: no selected primary measure favors '+other+'. '+rule]
            contrary=[r['phase'] for r in matrix if r['metric']=='PTS' and r['basis']=='totals' and r['complete'] and r['direction'] not in (direction,'tie')]
            if contrary:lines.append(other+' leads accumulated points in '+', '.join(contrary)+', but that does not overturn this rate-and-efficiency judgement.')
            return lines
        if not directions:return ['**Scoring verdict: no observed edge on the selected rate-and-efficiency measures.**',rule]
        return ['**Split scoring verdict: the selected rate-and-efficiency measures do not support one winner.**',
                'The advantages below depend on the metric or phase. Choosing an overall winner would require an additional priority, rather than a conclusion established by these data.']

    def answer_overview(self,matrix,verdict):
        c=self.contract
        labels={('PTS','totals'):'total points',('PTS','per_game'):'points per game',
                ('TS_PCT','per_game'):'true shooting',('WEIGHTED_RTS','per_game'):'league-relative efficiency'}
        phases=['Playoffs'] if c.lens=='postseason' else c.phases
        lines=self.scoring_position(matrix)
        if verdict=='insufficient_data':lines.append('**The available evidence cannot fully settle this comparison.**')
        elif c.request_kind=='claim':lines.append('Claim assessment: '+LABELS[verdict]+'.')
        for phase in phases:
            rows=[r for r in matrix if r['phase']==phase]
            if c.lens=='postseason':rows=[r for r in rows if r['basis']=='per_game' and r['metric'] in ('PTS','TS_PCT')]
            findings=[]
            for direction,pid in (('left',c.left_player),('right',c.right_player)):
                metrics=[labels[(r['metric'],r['basis'])] for r in rows if r['complete'] and r['direction']==direction]
                if metrics:findings.append(self.research.names[str(pid)]+' leads '+', '.join(metrics))
            tied=[labels[(r['metric'],r['basis'])] for r in rows if r['complete'] and r['direction']=='tie']
            if tied:findings.append('the players are tied on '+', '.join(tied))
            if findings:lines.append('**'+phase+': '+'; '.join(findings)+'.**')
        return lines

    def render_report(self,matrix,verdict,presentation,coverage):
        matrix=self.report_rows(matrix)
        c=self.contract;left=self.research.names[str(c.left_player)];right=self.research.names[str(c.right_player)]
        efficiency=any(r['metric'] in ('TS_PCT','WEIGHTED_RTS') for r in matrix)
        relative=any(r['metric']=='WEIGHTED_RTS' for r in matrix)
        title='Scoring Claim Review' if c.request_kind=='claim' else 'Scoring Comparison'
        lines=['# '+title,'','## Answer','',*self.answer_overview(matrix,verdict),'',
            '**Scope:** '+self.describe_scope()+'.','']
        methods=['','## Scope and methods','',
            '> '+re.sub(r'[\n\r<>]',' ',c.claim),'',f'- Subjects: **{left}** and **{right}**.',f'- Scope: {self.describe_scope()}.',
            f'- Statistical lens: {c.lens.replace("_"," ")}.',f'- Completed-season cutoff: **{season_label(c.cutoff)}**; ongoing seasons are excluded.',
            '- Metrics use summed source inputs. Missing observations remain missing.']
        if relative:methods.append('- Relative efficiency uses same-season, same-phase league TS; aggregation weights each season by FGA + 0.44 × FTA.')
        focus=[i for i in dict.fromkeys(presentation.highlight_rows) if 0<=i<len(matrix)][:3]
        if c.lens in ('volume','efficiency'):
            required=[('PTS','totals'),('PTS','per_game')] if c.lens=='volume' else [('TS_PCT','per_game'),('WEIGHTED_RTS','per_game')]
            essential=[next((i for i,r in enumerate(matrix) if (r['metric'],r['basis'])==key and r['complete']),None) for key in required]
            focus=list(dict.fromkeys([i for i in essential if i is not None]+focus))[:3]
        if c.lens=='postseason':
            essential=[i for i,r in enumerate(matrix) if r['phase']=='Playoffs' and r['basis']=='per_game' and r['metric'] in ('PTS','TS_PCT')]
            focus=essential[:2]
        if not focus:focus=[i for i,r in enumerate(matrix) if r['complete']][:2]
        directions={matrix[i]['direction'] for i in focus}
        counter=next((i for i,r in enumerate(matrix) if r['complete'] and r['direction'] in ('left','right') and r['direction'] not in directions
                      and (c.lens!='postseason' or (r['phase']=='Playoffs' and r['basis']=='per_game' and r['metric'] in ('PTS','TS_PCT')))),None)
        if counter is not None:
            if len(focus)==3:focus[-1]=counter
            else:focus.append(counter)
        if focus:
            lines+=['## Key evidence','']
            for index in focus:
                row=matrix[index]
                a=self.value(row['left_id'],row['metric']) if row['left_id'] else 'Unavailable'
                b=self.value(row['right_id'],row['metric']) if row['right_id'] else 'Unavailable'
                finding=f'{left} **{a}**; {right} **{b}**'
                qualifier='' if row['complete'] else ' (incomplete comparison)'
                lines.append(f"- **{row['phase']} / {row['label']} ({row['unit']})**: {finding}{qualifier}. "+self.cite(row['left_id'],row['right_id']))
        core=lines
        qualifications=[]
        lines=['',
            '## Comparable evidence','',f'| Phase | Statistical lens | {left} | {right} | Observed advantage | Sources |',
            '|---|---|---:|---:|---|---|']
        for row in matrix:
            a=self.value(row['left_id'],row['metric']) if row['left_id'] else 'Unavailable'
            b=self.value(row['right_id'],row['metric']) if row['right_id'] else 'Unavailable'
            direction={'left':left,'right':right,'tie':'Equal','unavailable':'Not fully comparable'}[row['direction']]
            lines.append(f"| {row['phase']} | {row['label']} ({row['unit']}) | {a} | {b} | {direction} | {self.cite(row['left_id'],row['right_id'])} |")
        lines+=['','## Sensitivity and counterevidence','']
        sensitivity=[]
        for phase in c.phases:
            selection={(r['metric'],r['basis']):r for r in matrix if r['phase']==phase}
            for a,b,label in ((('PTS','totals'),('PTS','per_game'),'Accumulation versus scoring rate'),
                              (('TS_PCT','per_game'),('WEIGHTED_RTS','per_game'),'Raw versus contemporaneous relative efficiency')):
                if a not in selection or b not in selection:continue
                first,second=selection[a],selection[b]
                if not first['complete'] or not second['complete']:
                    text=f'{phase}: {label.lower()} cannot be fully tested because the required comparable evidence is incomplete.'
                    state='insufficient'
                else:
                    def outcome(row):
                        return 'is tied' if row['direction']=='tie' else 'favors '+(left if row['direction']=='left' else right)
                    text=f"{phase}: the {first['label'].lower()} comparison {outcome(first)}; the {second['label'].lower()} comparison {outcome(second)}. "
                    if first['metric']=='PTS':text+='Accumulation and scoring rate answer different questions.'
                    else:text+='Raw conversion and performance above the contemporary league answer different questions.'
                    state='changes' if first['direction']!=second['direction'] else 'stable'
                sensitivity.append({'phase':phase,'test':label,'result':state})
                note='- '+text+' '+self.cite(first['left_id'],first['right_id'],second['left_id'],second['right_id'])
                lines.append(note)
                if state=='changes':qualifications.append(note)
        if set(c.phases)=={'Regular Season','Playoffs'}:
            change_keys=[key for key in ('PTS','TS_PCT') if any(r['metric']==key and r['basis']=='per_game' for r in matrix)]
            labels={'PTS':'Points-per-game change','TS_PCT':'TS change (percentage points)'}
            lines+=['','### Regular-season to postseason changes','',
                    '| Subject | '+' | '.join(labels[key] for key in change_keys)+' | Sources |',
                    '|---|'+'---:|'*len(change_keys)+'---|']
            evidence=self.current_evidence()
            changes={}
            for pid in (c.left_player,c.right_player):
                records={r['scope']['phase']:r for r in evidence.values() if r.get('kind')=='scoring_stats' and r.get('player_id')==pid and r['scope']['basis']=='per_game'}
                if len(records)!=2:continue
                regular,post=records['Regular Season'],records['Playoffs']
                vals={}
                for key in change_keys:
                    a,b=regular['values'][key],post['values'][key]
                    val=b['value']-a['value'] if a['complete'] and b['complete'] and a['value'] is not None and b['value'] is not None else None
                    vals[key+'_CHANGE']={'value':val,'label':key+' postseason change','unit':'percentage points' if key=='TS_PCT' else 'points/game',
                        'formula':'postseason value - corresponding regular-season value','inputs':{'regular':a['value'],'postseason':b['value']}}
                rec=self.research.add({'kind':'scoring_change','player_id':pid,'player_name':self.research.names[str(pid)],
                    'scope':post['scope'],'values':vals,'sources':regular['sources']+post['sources'],
                    'limitations':['Different game samples and opposition; the difference is descriptive, not a causal estimate.']})
                self.research.used_evidence.add(rec['id'])
                changes[pid]=rec
                lines.append('| '+rec['player_name']+' | '+' | '.join(self.value(rec['id'],key+'_CHANGE') for key in change_keys)+' | '+self.cite(rec['id'])+' |')
            for key in change_keys:
                row=next((r for r in matrix if r['phase']=='Playoffs' and r['metric']==key and r['basis']=='per_game'),None)
                records=[changes.get(pid) for pid in (c.left_player,c.right_player)]
                values=[rec['values'][key+'_CHANGE']['value'] if rec else None for rec in records]
                if not row or not row['complete'] or any(value is None for value in values):continue
                direction='left' if values[0]>values[1] else 'right' if values[0]<values[1] else 'tie'
                level='is tied' if row['direction']=='tie' else 'favors '+(left if row['direction']=='left' else right)
                change='is tied' if direction=='tie' else 'favors '+(left if direction=='left' else right)
                text=f"The playoff {row['label'].lower()} comparison {level}; the playoff-minus-regular-season change {change}. "
                text+='A higher playoff level is not the same as a larger change from the regular season. Different games and opposition prevent a causal interpretation.'
                note='- '+text+' '+self.cite(row['left_id'],row['right_id'],*(rec['id'] for rec in records))
                lines.append(note)
                if c.lens=='postseason':
                    values_text='; '.join(rec['player_name']+' **'+self.value(rec['id'],key+'_CHANGE')+'**' for rec in records)
                    main_note='- **'+labels[key]+'**: '+values_text+'. The larger change '+change+'. '+self.cite(*(rec['id'] for rec in records))
                    if row['direction']!=direction:qualifications.insert(0,main_note)
                    else:qualifications.append(main_note)
                elif row['direction']!=direction:qualifications.insert(0,note)
                sensitivity.append({'phase':'Playoffs','test':row['label']+' level versus phase change',
                                    'result':'changes' if row['direction']!=direction else 'stable'})
        self.render_context(lines)
        lines+=['','## Coverage and limits','']
        for cell in coverage:lines.append(f"- **{cell['dimension'].title()}: {cell['status']}** — {cell['reason']}")
        for result in self.results.values():
            for issue in result.get('gaps',[]):lines.append('- '+issue['subject']+': '+issue['reason'])
        for r in self.current_evidence().values():
            if relative and r.get('kind')=='scoring_relative':
                lines.append(f"- {r['player_name']}, {r['scope']['phase']}: league-baseline shooting-opportunity coverage **{self.value(r['id'],'ERA_COVERAGE')}%**. "+self.cite(r['id']))
        if relative:lines.append('- Era-relative TS is a descriptive benchmark, not a causal correction for rules, physicality, spacing or defensive difficulty.')
        if efficiency:lines.append('- True shooting uses the conventional 0.44 free-throw coefficient. It estimates shooting opportunities rather than counting actual possessions.')
        if c.include_context:lines.append('- Supporting-cast cases and opponent records are contextual samples. No teammate-swap or championship-credit calculation is justified.')
        lines+=[
                '- Linked evidence records retain exact scope, formulas, season inputs, original API parameters and retrieval timestamps. Aggregate citations use multiple API inputs; inspect the full source set in the evidence panel.',
                '- No total player score is produced. All displayed advantages are specific to a metric and sample.']
        if any(cell['status']!='completed' for cell in coverage):
            qualifications.insert(0,'- Some requested evidence remains incomplete. Read the coverage details before treating the available findings as a full answer.')
        if qualifications:core+=['','## What changes the interpretation?','',*qualifications[:3]]
        if self.content_checks:
            core+=['','## Why we investigated further','']
            for check in self.content_checks[:2]:
                outcome={'completed':'Finding checked','retryable':'Still unresolved','unavailable':'Evidence remains limited'}[check['status']]
                core+=['- **Finding:** '+check['reason'],
                    '- **'+outcome+':** '+check.get('resolution','The investigation has not resolved this gap.')+' '+self.cite(*(check['evidence_ids']+check.get('added_evidence_ids',[])))]
            core+=['','These checks qualify supporting-cast context; they do not change the focal-player scoring totals or establish why a player missed games.']
        core+=['','These findings compare the selected scoring measures; they do not establish overall ability or explain championship outcomes.']
        return '\n'.join(core+lines+methods),sensitivity

    def render_context(self,lines):
        if not self.contract.include_context:
            return
        support=self.results.get('collect_scoring_support',{})
        lines+=['','## Core helpers and rotation context','',
            'The same anchor rule is used for both subjects: earliest and latest verified Finals in the approved window, otherwise recorded playoff endpoints. These are case studies, not complete-career teammate rankings.','',
            '| Focal player / sample | Core helper candidate | PPG | MPG | Recorded games | TS% | Sources |','|---|---|---:|---:|---:|---:|---|']
        for sample in support.get('samples',[]):
            if sample['phase'] not in (self.contract.support_phases or self.contract.phases) or not sample_scope_matches(sample,self.research.evidence):continue
            for ident in sample['core']:
                r=self.research.evidence[ident]
                lines.append(f"| {self.research.names[str(sample['player_id'])]} / {season_label(sample['season'])} / {sample['phase']} | {r['player_name']} | {self.value(ident,'PTS')} | {self.value(ident,'MIN')} | {self.value(ident,'GP')} | {self.value(ident,'TS_PCT')} | {self.cite(ident)} |")
        if not support.get('samples'):
            lines+=['','No verified supporting-cast samples were returned. This does not establish that either player lacked support.']
        lines+=['','Core candidates are selected by contemporary scoring production, not by career reputation or an overall ability score. The main rotation is retained by total minutes; its full minutes, production and availability rows appear in the supporting-cast details below the report. Games played do not identify injuries or actual shared court time.']
        self.render_content_followups(lines)
        finals=self.results.get('collect_scoring_finals',{})
        lines+=['','## Finals opposition within the selected scope','',
            '| Subject | Season | Opponent | Team series W–L | Player PPG | Player TS% | Opponent regular-season win% | Sources |',
            '|---|---|---|---:|---:|---:|---:|---|']
        for r in finals.get('records',[]):
            ident=r['id']
            lines.append(f"| {r['player_name']} | {season_label(r['scope']['start'])} | {r['context']['opponent_name']} | {self.value(ident,'SERIES_WINS')}–{self.value(ident,'SERIES_LOSSES')} | {self.value(ident,'PTS')} | {self.value(ident,'TS_PCT')} | {self.value(ident,'OPP_WIN_PCT')} | {self.cite(ident)} |")
        for pid in (self.contract.left_player,self.contract.right_player):
            if not any(r['player_id']==pid for r in finals.get('records',[])):
                lines+=['',self.research.names[str(pid)]+': no verified Finals series was returned inside this scope; inspect coverage gaps before interpreting this absence.']
        lines+=['','Opponent regular-season record is one limited proxy. Finals wins and defeats are included; Finals-only player data must not be described as the whole postseason.']

    def render_content_followups(self,lines):
        if not self.content_checks:return
        lines+=['','### Evidence-driven supporting-cast checks','',
            'The Lead checked whether the retrieved helper samples answer the question, in addition to checking whether the collectors ran. A candidate with fewer than half the maximum recorded games in the returned rotation triggers a sample-adequacy check; this is a declared screening rule, not a teammate ranking or exclusion threshold.','']
        for check in self.content_checks:
            status={'completed':'Addressed','retryable':'Not completed within the remaining run budget','unavailable':'Limited by scope or source coverage'}[check['status']]
            lines.append('- **'+status+'**: '+check['reason']+' '+check.get('resolution','')+' '+self.cite(*(check['evidence_ids']+check.get('added_evidence_ids',[]))))
        added=[];seen=set()
        for result in self.content_results.values():
            for issue in result.get('gaps',[]):lines.append('- Targeted source gap: '+issue['reason'])
            for sample in result.get('samples',[]):
                if sample_key(sample) not in seen:added.append(sample);seen.add(sample_key(sample))
        if added:
            lines+=['','Matched additional samples are shown alongside the original observations. Regular-season context describes a different sample; it does not replace postseason availability.','',
                '| Subject / added sample | Core helper candidate | PPG | MPG | Recorded games | TS% | Sources |','|---|---|---:|---:|---:|---:|---|']
            for sample in added:
                for ident in sample['core']:
                    r=self.research.evidence[ident]
                    lines.append(f"| {self.research.names[str(sample['player_id'])]} / {season_label(sample['season'])} / {sample['phase']} | {r['player_name']} | {self.value(ident,'PTS')} | {self.value(ident,'MIN')} | {self.value(ident,'GP')} | {self.value(ident,'TS_PCT')} | {self.cite(ident)} |")

    def publish(self):
        self.refresh_content_checks()
        self.emit({'type':'phase','label':'Writer: auditing the scoring claim against verified comparisons'})
        evidence_matrix=scoring_matrix(self.current_evidence(),self.contract)
        verdict=adjudicate(evidence_matrix,self.contract)
        public_verdict='comparison' if self.contract.request_kind=='comparison' and verdict!='insufficient_data' else verdict
        matrix=self.report_rows(evidence_matrix)
        coverage=self.coverage()
        writer=ActivityLog(self.emit,agent='Writer',node_id='writer')
        try:
            presentation=self.structured(SCORING_WRITER+'\nCONTRACT:\n'+self.contract.model_dump_json()+
                '\nMATRIX:\n'+json.dumps(matrix)+'\nRESULT TYPE:\n'+public_verdict+'\nCOVERAGE:\n'+json.dumps(coverage),ScoringPresentation)
        except Exception:
            presentation=ScoringPresentation(emphasis='coverage_first',caveats=['partial_coverage'])
        self.scoring_judgement_review=[]
        if self.contract.lens=='overall_scoring':
            from types import SimpleNamespace
            from backend.research.judgement import decide, render as render_judgement
            adapter=SimpleNamespace(p=self,c=self.contract,results={})
            ledger=[dict(r,id=f"scoring:{r['phase']}:{r['metric']}:{r['basis']}",dimension='offense',evidence_ids=[i for i in (r['left_id'],r['right_id']) if i]) for r in matrix]
            judgement,rows,self.scoring_judgement_review=decide(adapter,ledger)
            adapter.judgement_attempts=self.scoring_judgement_review
            if judgement:self.reviewed_scoring_position=render_judgement(adapter,judgement,rows)
        writer.start('compose_scoring_review',{})
        answer,sensitivity=self.render_report(matrix,verdict,presentation,coverage)
        cards=[];errors=[]
        claims=list({c.model_dump_json():c for c in self.published_claims}.values())
        for index in range(0,len(claims),8):
            checked=self.research.audit_argument(Audit(claims=claims[index:index+8]))
            cards+=checked['cards'];errors+=checked['errors']
        writer.append({'name':'compose_scoring_review','args':{},'result':json.dumps({
            'verdict':public_verdict,'valid':not errors,'checked_claims':len(cards),'presentation':presentation.model_dump(),'judgement_review':self.scoring_judgement_review,'errors':errors})})
        self.log.extend(writer)
        if errors:raise ValueError('The deterministic scoring report failed its evidence audit.')
        sources={json.dumps(s,sort_keys=True):s for r in self.current_evidence().values() for s in r.get('sources',[])}
        limitations=list(dict.fromkeys(l for r in self.current_evidence().values() for l in r.get('limitations',[])))
        support=self.results.get('collect_scoring_support',{})
        support_details=[]
        samples=support.get('samples',[])+[s for result in self.content_results.values() for s in result.get('samples',[])]
        seen=set()
        for sample in samples:
            key=(sample_key(sample),bool(sample.get('followup')))
            if key in seen:continue
            seen.add(key)
            support_details.append(dict(sample,player_name=self.research.names[str(sample['player_id'])],
                rotation_records=[dict(compact(self.research.evidence[i]),
                    evidence_url=f"/sessions/{self.research.session_id}/evidence/{i}" if getattr(self.research,'session_id',None) else None)
                    for i in sample['rotation']]))
        self.research.research_summary={'cards':cards,'comparisons':[],'sources':list(sources.values()),'limitations':limitations,
            'verification':{'status':'checked' if cards else 'not_submitted','checked_claims':len(cards),'attempts':[{'valid':True,'errors':[]}],
                'note':'Published numeric values and comparison directions are server-derived and checked against scoped evidence. Missing source coverage is reported separately; descriptive context does not establish causation.'},
            'research':{'scope':self.describe_scope(),'criteria':'Cross-era scoring claim review','tasks':self.tasks,
                'findings':self.findings,'coverage':'completed' if all(c['status']=='completed' for c in coverage) else 'partial',
                'content_checks':self.content_checks,
                'coverage_cells':coverage,'elapsed_seconds':round(time.monotonic()-self.started,2),'api_requests':self.data.requests,
                'tokens':self.tokens,'data_cutoff':datetime.now(timezone.utc).isoformat(),
                'limits':{'seconds':240,'researchers':8,'rounds':3,'parallel_workers':4}},
            'scoring':{'contract':self.contract.model_dump(),'verdict':public_verdict,'matrix':matrix,
                       'sensitivity':sensitivity,'support_samples':support_details,'presentation':presentation.model_dump()}}
        self.research.submission={'answer':answer,'cards':cards}
        return answer

    def run(self,lookup=None):
        self.flow.add('lead','Lead','lead','Lead',description='Confirm the scoring claim, identities and scope; plan independent investigations.')
        try:
            return self.run_with_flow(lookup)
        except Exception:
            self.flow.close('failed')
            raise

    def run_with_flow(self,lookup=None):
        self.emit({'type':'phase','label':'Lead: confirming the scoring claim and comparison contract'})
        self.contract=self.resolve_contract()
        self.record_lead('confirm_scoring_contract',self.contract.model_dump())
        if self.contract.action!='review':
            defaults={
                'clarify':'Name two players and choose career scoring or two equal-length season windows, then specify volume, efficiency, or both.',
                'outside_scope':'This assistant investigates NBA on-court contributions between two players. Ask about scoring, playmaking, defensive evidence or team on/off; cultural influence, overall greatness, predictions and profiles are outside its scope.',
                'unsupported_era':'This version supports comparisons starting with 1984-85. Earlier periods have insufficient validated coverage; please choose a supported window.',
                'causal_limit':'Scoring and teammate statistics cannot prove hypothetical championship outcomes after swapping teammates. I can review an observed scoring claim and describe bounded supporting-cast context instead.'}
            answer=self.contract.question or defaults[self.contract.action]
            if self.contract.action=='clarify' and not self.contract.question and len(self.research.names)==2:
                answer='For '+ ' and '.join(self.research.names.values())+', choose complete-career scoring or explicit equal-length season windows, then scoring volume, shooting efficiency, or both.'
            self.flow.finish('lead',summary=answer,tool_ids=[call['id'] for call in self.log])
            self.flow.close('clarification' if self.contract.action=='clarify' else 'outside_scope')
            return answer,self.log
        if self.contract.research_domain=='on_court':
            from backend.research.impact import ImpactInvestigation
            return ImpactInvestigation(self).run()
        decision=self.decision()
        self.flow.finish('lead',summary=self.describe_scope(),tool_ids=[call['id'] for call in self.log])
        for round_number in range(1,4):
            self.fan_out(decision,round_number)
            if len(self.tasks)>=8 or time.monotonic()>self.deadline-65:break
            review=f'review-{round_number}'
            self.flow.add(review,'Lead review','review','Lead',self.flow_frontier,
                'Inspect collected evidence and decide whether targeted follow-up is needed.',round_number)
            self.lead_log.node_id=review
            start=len(self.log)
            decision=self.decision(review=True)
            gaps=[c['reason'] for c in self.coverage() if c['status']=='retryable']
            summary=('Follow-up requested: '+' '.join(gaps)) if decision.action=='research' else 'Evidence review complete; proceed with the available coverage and disclosed gaps.'
            if round_number==3 and decision.action=='research':summary='The research-round cap was reached. The report will disclose the remaining evidence gaps.'
            self.flow.finish(review,summary=summary,tool_ids=[call['id'] for call in self.log[start:]])
            self.flow_frontier=[review]
            if decision.action=='finish':break
        self.flow.add('writer','Writer','writer','Writer',self.flow_frontier,
            'Select evidence and counterevidence; render and audit the sourced report.')
        answer=self.publish()
        self.flow.finish('writer',summary='The report passed its numerical evidence checks.',
            tool_ids=[call['id'] for call in self.log if call.get('agent')=='Writer'])
        self.flow.close('completed' if all(c['status']=='completed' for c in self.coverage()) else 'partial')
        return answer,self.log
