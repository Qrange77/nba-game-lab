"""Natural-question checks; preserve initial defects and final reruns separately."""
import argparse
import json
from pathlib import Path
from backend.assistant.research_tools import AssistantResearchTools
from backend.research.scoring import ScoringRun
from test.paired_benchmark import Recorder
CASES=[('broad','Who had more impact on the court: Michael Jordan in 1990-91 or LeBron James in 2014-15?',[(893,'Michael Jordan'),(2544,'LeBron James')]),('playmaking','Who helped their teammates more in 2015-16, Curry or LeBron?',[(201939,'Stephen Curry'),(2544,'LeBron James')]),('defense','Who was the better defender: Duncan in 2002-03 or Garnett in 2003-04?',[(1495,'Tim Duncan'),(708,'Kevin Garnett')]),('team','Whose team depended on him more in 2015-16: Curry or LeBron?',[(201939,'Stephen Curry'),(2544,'LeBron James')]),('scoring','Who was the better scorer: Kobe in 2005-06 or Curry in 2015-16?',[(977,'Kobe Bryant'),(201939,'Stephen Curry')])]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--folder',required=True);parser.add_argument('--case');args=parser.parse_args();folder=Path(args.folder);folder.mkdir(parents=True,exist_ok=True)
 for ident,q,players in CASES:
  if args.case and args.case!=ident:continue
  path=folder/(ident+'.json')
  if path.exists():raise FileExistsError(path)
  r=AssistantResearchTools(players=[dict(id=i,name=n) for i,n in players],question=q);rec=Recorder();run=ScoringRun([dict(role='user',content=q)],r,complete=rec)
  answer,calls=run.run();d=dict(question=q,answer=answer,contract=run.contract.model_dump(),evidence_result=r.summary() if r.submission else None,model_calls=rec.calls,tool_calls=calls)
  path.write_text(json.dumps(d,indent=2)+'\n')
  (folder/(ident+'.md')).write_text('# '+q+'\n\n'+answer+'\n')
  print(ident,answer.split('## Dimension findings')[0][:2000],flush=True)
if __name__=='__main__':main()
