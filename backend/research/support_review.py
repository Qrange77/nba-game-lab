"""Evidence sufficiency checks for bounded supporting-cast research.

These checks identify research questions, not teammate quality or injury causes.
The appearance screen is declared, symmetric, and never deletes original rows.
"""
import hashlib
import json

KEYS=('PTS','MIN','GP','TS_PCT')


def sample_key(sample):
    return sample['player_id'],sample['season'],sample['phase']


def sample_scope_matches(sample,evidence):
    ids=list(dict.fromkeys(sample.get('core',[])+sample.get('rotation',[])))
    return bool(ids) and all(i in evidence and evidence[i].get('scope',{}).get('start')==sample['season']
        and evidence[i]['scope'].get('end')==sample['season'] and evidence[i]['scope'].get('phase')==sample['phase']
        and evidence[i].get('context',{}).get('focal_player_id')==sample['player_id'] for i in ids)


def complete_sample(sample,evidence):
    core=sample.get('core',[])
    return sample_scope_matches(sample,evidence) and bool(core and sample.get('rotation')) and all(
        evidence.get(ident,{}).get('values',{}).get(key,{}).get('complete',False)
        for ident in core for key in KEYS)


def supporting_cast_gaps(contract,samples,evidence):
    """Return grounded inquiries whose proposed targets stay in the contract."""
    if not contract.include_context:return []
    approved_phases=contract.support_phases or contract.phases
    subjects=(contract.left_player,contract.right_player)
    anchors={pid:sorted((s for s in samples if s['player_id']==pid),key=lambda s:s['season']) for pid in subjects}
    gaps={}

    def matched_targets(sample,phase,source='default'):
        targets=[]
        for pid in subjects:
            if contract.period=='windows':
                origin=contract.bounds(sample['player_id'])[0]
                year=contract.bounds(pid)[0]+sample['season']-origin
            else:
                own=sorted({s['season'] for s in anchors[sample['player_id']]});other=sorted({s['season'] for s in anchors[pid]})
                if not other:return []
                index=own.index(sample['season'])
                year=other[0 if index==0 else -1]
            lo,hi=contract.bounds(pid)
            if not lo<=year<=hi or phase not in approved_phases:return []
            targets.append({'player_id':pid,'season':year,'phase':phase,'source':source})
        return targets

    def add(sample,kind,reason,ids,phase,source='default'):
        targets=matched_targets(sample,phase,source)
        key=json.dumps([kind,targets or [sample_key(sample)]],sort_keys=True)
        ident='content_'+hashlib.sha256(key.encode()).hexdigest()[:16]
        if ident in gaps:
            gaps[ident]['evidence_ids']=sorted(set(gaps[ident]['evidence_ids']+ids));return
        gaps[ident]={'id':ident,'dimension':'teammates','kind':kind,'reason':reason,
            'evidence_ids':ids,'targets':targets,
            'question':'Check whether the original helper sample is adequate by retrieving the approved matched supporting-cast samples. Preserve original evidence and separate phases.',
            'status':'retryable' if targets else 'unavailable',
            'resolution':'' if targets else 'A matched additional sample is outside the approved phases or unavailable from the verified anchor inventory. Retain the original sample and its limitation.'}

    for sample in samples:
        original=list(dict.fromkeys(sample.get('core',[])+sample.get('rotation',[])))
        records=[evidence[i] for i in original if i in evidence]
        if sample['phase'] not in approved_phases:
            add(sample,'phase_mismatch','The initial helper sample uses a different phase from the approved supporting-cast comparison.',original,approved_phases[0]);continue
        if not complete_sample(sample,evidence):
            add(sample,'missing_helper_metrics','The helper sample lacks comparable core production, minutes, games or shooting inputs. Check an alternate roster/career source.',original,sample['phase'],'roster')
        appearances=[(r['values']['GP']['value'],r['id']) for r in records
            if r.get('values',{}).get('GP',{}).get('complete') and r['values']['GP']['value'] is not None]
        if not appearances:continue
        largest,largest_id=max(appearances)
        sparse=[i for i in sample.get('core',[]) if i in evidence and
            evidence[i].get('values',{}).get('GP',{}).get('value') is not None and
            0<evidence[i]['values']['GP']['value']<largest/2]
        if sparse and sample['phase']=='Playoffs':
            names=', '.join(evidence[i]['player_name'] for i in sparse)
            add(sample,'sparse_helper_sample',
                'The per-game core list includes '+names+' with sparse recorded appearances relative to the returned rotation. A matched regular-season baseline is needed before treating this playoff sample as typical supporting-cast context.',
                list(dict.fromkeys(sparse+[largest_id])),'Regular Season')
    return list(gaps.values())


def assess_support_gaps(gaps,evidence,available_samples,results,attempts):
    """Reuse scoped evidence first; exhausted alternatives remain limitations."""
    by_scope={}
    for sample in available_samples:
        key=sample_key(sample)
        if key not in by_scope or complete_sample(sample,evidence):by_scope[key]=sample
    for gap in gaps:
        if not gap['targets']:continue
        matching=[by_scope.get((t['player_id'],t['season'],t['phase'])) for t in gap['targets']]
        # An alternate-source inquiry cannot be satisfied by the same incomplete
        # rows that triggered it. Matching rows must now contain every metric.
        if all(s is not None and complete_sample(s,evidence) for s in matching):
            conflicts=[]
            if gap['kind']=='missing_helper_metrics':
                new=[evidence[i] for s in matching for i in dict.fromkeys(s.get('core',[])+s.get('rotation',[]))]
                for ident in gap['evidence_ids']:
                    old=evidence.get(ident,{})
                    for other in new:
                        if old.get('player_id')!=other.get('player_id') or old.get('scope')!=other.get('scope') or any(old.get('context',{}).get(k)!=other.get('context',{}).get(k) for k in ('team_id','focal_player_id')):continue
                        for key in KEYS:
                            a=old.get('values',{}).get(key,{});b=other.get('values',{}).get(key,{})
                            if a.get('complete') and b.get('complete') and a.get('value') is not None and b.get('value') is not None and abs(a['value']-b['value'])>1e-7:
                                conflicts.append({'original_id':ident,'alternate_id':other['id'],'metric':key})
            if conflicts:
                gap.update(status='unavailable',resolution='The alternate source disagrees with a previously available scoped metric. Both source records are retained; the discrepancy has not been silently reconciled.',
                    conflicts=conflicts,added_evidence_ids=list(dict.fromkeys(c['alternate_id'] for c in conflicts)))
                continue
            gap.update(status='completed',resolution='Matched scoped evidence addresses the sample-adequacy question. Original observations remain visible; the additional phase does not replace them.',
                reused=gap['id'] not in results,
                added_evidence_ids=list(dict.fromkeys(i for s in matching for i in s.get('core',[]))))
        elif gap['id'] in results:
            gap.update(status='unavailable',resolution='The targeted source check did not return all required comparable helper samples. Its exact gaps remain disclosed; do not infer injuries or a complete-career support ranking.')
        elif attempts.get(gap['id'],0)>=2:
            gap.update(status='unavailable',resolution='The targeted investigation did not complete within its attempt cap; retain the evidence limitation.')
    return gaps
