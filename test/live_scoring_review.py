"""Opt-in real-model acceptance cases for the focused scoring reviewer."""
import argparse
import json
import time
from threading import Lock
from types import SimpleNamespace
from pathlib import Path
import litellm
from app import run_agent, SYSTEM_PROMPT
from backend.assistant.research_tools import AssistantResearchTools
from backend.research.engine import MODEL
from backend.research.scoring import ScoringRun


def main():
    cases=json.loads(Path(__file__).with_name('scoring_cases.json').read_text())
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',required=True,choices=[c['id'] for c in cases])
    parser.add_argument('--baseline',action='store_true')
    parser.add_argument('--output-dir',default='output/scoring-review')
    parser.add_argument('--inject-gap',action='store_true',help='Omit the first personal collector in a controlled fault test; all other model/data calls remain live.')
    parser.add_argument('--record-contexts',action='store_true',help='Record public first-call context metadata for each researcher; do not change its model request.')
    args=parser.parse_args()
    case=next(c for c in cases if c['id']==args.case)
    research=AssistantResearchTools(players=[{'id':p,'name':n} for p,n in case['players']],question=case['question'])
    flow_events=[]
    def event(e):
        if e['type']=='research_flow':flow_events.append(e['flow'])
        if e['type'] in ('phase','research_plan','research_task'):
            print(json.dumps(e),flush=True)
    start=time.monotonic()
    messages=[{'role':'system','content':SYSTEM_PROMPT},{'role':'user','content':case['question']}]
    injected=False;lock=Lock();contexts=[]
    def complete(**kwargs):
        nonlocal injected
        ms=kwargs['messages']
        if args.record_contexts and len(ms)==2 and 'independent NBA scoring researcher' in ms[0].get('content',''):
            payload=json.loads(ms[1]['content'])
            with lock:
                contexts.append({'dimension':payload['task']['dimension'],'gap_id':payload['task'].get('gap_id',''),
                    'initial_messages':len(ms),'roles':[m['role'] for m in ms],
                    'payload_fields':sorted(payload),'original_evidence_ids':[r['id'] for r in payload['original_evidence']],
                    'assigned_collector':payload['required_collector'],
                    'other_researcher_conversations_included':False})
        if args.inject_gap and len(ms)==2 and 'independent NBA scoring researcher' in ms[0].get('content',''):
            task=json.loads(ms[1]['content'])['task']
            with lock:
                if task['dimension']=='personal' and not injected:
                    injected=True
                    message=SimpleNamespace(content='Controlled test interruption before required data collection.',tool_calls=None)
                    message.model_dump=lambda:{'role':'assistant','content':message.content}
                    return SimpleNamespace(choices=[SimpleNamespace(message=message)],usage=None)
        return litellm.completion(**kwargs)
    if args.inject_gap or args.record_contexts:
        response,calls=ScoringRun(messages,research,event,complete=complete).run()
    else:
        response,calls=run_agent(messages,research=research,on_event=event)
    result_id=case['id']+('-gap' if args.inject_gap else '')
    result={'id':result_id,'question':case['question'],'expected':case['expected'],'response':response,
        'research_flow':flow_events[-1] if flow_events else None,'flow_events':flow_events,
        'tool_calls':calls,'evidence':research.evidence,'evidence_result':research.summary() if research.used_evidence or research.submission else None,
        'seconds':round(time.monotonic()-start,2),'model':MODEL,'controlled_gap_injected':injected,
        'researcher_initial_contexts':contexts if args.record_contexts else None}
    folder=Path(args.output_dir);folder.mkdir(parents=True,exist_ok=True)
    if args.baseline:
        raw=litellm.completion(model=MODEL,vertex_location='global',messages=[{'role':'user','content':case['question']}],
            max_tokens=2400,timeout=40,num_retries=0)
        result['no_tools_no_system_answer']=raw.choices[0].message.content
    (folder/(result_id+'.json')).write_text(json.dumps(result,indent=2))
    if args.baseline:
        public={k:v for k,v in result.items() if k!='evidence'}
        public['tool_calls']=[{k:v for k,v in call.items() if k!='result'} for call in calls]
        summary=result['evidence_result'] or {}
        public['evidence_result']={k:summary[k] for k in ('verification','research','scoring') if k in summary}
        public['note']='Full numeric cards, original evidence and collector responses are retained in the ignored local output artifact. This snapshot preserves both complete answers, the comparison matrix and activity metadata.'
        Path('docs/examples').mkdir(parents=True,exist_ok=True)
        Path(f'docs/examples/{case["id"]}.json').write_text(json.dumps(public,indent=2))
    print(json.dumps({'id':case['id'],'seconds':result['seconds'],
        'verdict':(result['evidence_result'] or {}).get('scoring',{}).get('verdict'),
        'coverage':(result['evidence_result'] or {}).get('research',{}).get('coverage'),
        'verification':(result['evidence_result'] or {}).get('verification'),
        'response_start':response[:160]}),flush=True)


if __name__=='__main__':main()
