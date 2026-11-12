"""Opt-in real-model clarification checks; not part of the frozen benchmark."""
import argparse
import json
from pathlib import Path

from backend.assistant.research_tools import AssistantResearchTools
from backend.research.engine import MODEL
from backend.research.scoring import ScoringRun
from test.paired_benchmark import Recorder, raw_request


CASES = {
    'ability': ('Compare Michael Jordan and LeBron James on scoring ability.',
                'Use Jordan in 1990-91 and James in 2014-15.'),
    'influence': ('Compare Michael Jordan and LeBron James on influence.',
                  'I mean observed scoring performance. Use Jordan in 1990-91 and James in 2014-15.'),
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=CASES, required=True)
    parser.add_argument('--output-dir', default='output/ambiguity-review')
    args = parser.parse_args()
    question, clarification = CASES[args.case]
    messages = []
    turns = []
    for text in (question, clarification):
        messages.append({'role': 'user', 'content': text})
        research = AssistantResearchTools(players=[{'id': 893, 'name': 'Michael Jordan'},
                                                   {'id': 2544, 'name': 'LeBron James'}], question=text)
        recorder = Recorder()
        run = ScoringRun(messages.copy(), research, complete=recorder)
        answer, calls = run.run()
        turns.append({'user': text, 'answer': answer, 'contract': run.contract.model_dump(),
                      'tool_calls': calls, 'model_calls': recorder.calls, 'tasks': run.tasks,
                      'flow': run.flow.snapshot(), 'evidence': research.evidence,
                      'evidence_result': research.summary() if research.submission else None})
        messages.append({'role': 'assistant', 'content': answer})
    # Raw receives the initial question alone, then the same question plus the
    # user's scope clarification in a separate, single-user-message request.
    # It never receives Agent's clarification wording, findings or sources.
    raw = []
    for text in (question, question + '\n\n' + clarification):
        recorder = Recorder()
        response = recorder(**raw_request(text, MODEL))
        raw.append({'question': text, 'answer': response.choices[0].message.content,
                    'model_calls': recorder.calls})
    folder = Path(args.output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    result = {'case': args.case, 'turns': turns, 'raw': raw,
              'note': 'Exploratory clarification comparison, not a scored superiority claim. Raw uses one user message per request, no tools or system prompt. Agent receives its own clarification history. No faults or extra rounds are injected.'}
    (folder / (args.case + '.json')).write_text(json.dumps(result, indent=2) + '\n')
    assert turns[0]['contract']['action'] == 'clarify', turns[0]['contract']
    assert not turns[0]['tasks'] and not turns[0]['evidence']
    assert turns[1]['contract']['action'] == 'review', turns[1]['contract']
    initial = [task for task in turns[1]['tasks'] if task['round'] == 1]
    assert {task['dimension'] for task in initial} == {'personal', 'era', 'teammates', 'opponents'}
    assert len(initial) == 4
    assert turns[1]['evidence_result']['verification']['status'] == 'checked'
    print(json.dumps({'case': args.case, 'status': 'passed', 'clarification': turns[0]['answer'],
                      'initial_researchers': len(initial), 'total_researchers': len(turns[1]['tasks']),
                      'raw_calls': [len(r['model_calls']) for r in raw]}))


if __name__ == '__main__':
    main()
