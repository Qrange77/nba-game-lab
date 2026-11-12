"""Predeclared on-court paired checks; preserve every answer, including failures."""
import argparse
import json
from pathlib import Path
from backend.assistant.research_tools import AssistantResearchTools
from backend.research.engine import MODEL
from backend.research.scoring import ScoringRun
from test.paired_benchmark import Recorder, raw_request

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case');parser.add_argument('--output-dir',default='docs/impact-review');args=parser.parse_args()
    folder=Path(args.output_dir);folder.mkdir(parents=True,exist_ok=True)
    for case in json.loads(Path('test/impact_cases.json').read_text()):
        if args.case and case['id']!=args.case:continue
        path=folder/(case['id']+'.json')
        if path.exists():raise FileExistsError('Preserve saved answers; choose a new output directory: '+str(path))
        recorder=Recorder();research=AssistantResearchTools(players=[{'id':p,'name':n} for p,n in case['players']],question=case['question'])
        run=ScoringRun([{'role':'user','content':case['question']}],research,complete=recorder)
        result={'case':case,'model':MODEL}
        try:
            answer,calls=run.run()
            result.update(answer=answer,contract=run.contract.model_dump(),tool_calls=calls,model_calls=recorder.calls,tasks=run.tasks,flow=run.flow.snapshot(),evidence=research.evidence,evidence_result=research.summary() if research.submission else None)
        except Exception as exc:result.update(error=str(exc),model_calls=recorder.calls)
        path.write_text(json.dumps(result,indent=2)+'\n')
        raw=Recorder()
        try:
            response=raw(**raw_request(case['question'],MODEL));result['raw']={'answer':response.choices[0].message.content,'model_calls':raw.calls}
        except Exception as exc:result['raw']={'error':str(exc),'model_calls':raw.calls}
        path.write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'case':case['id'],'error':result.get('error'),'contract':result.get('contract'),'tasks':result.get('tasks'),'verification':(result.get('evidence_result') or {}).get('verification')}),flush=True)
if __name__=='__main__':main()
