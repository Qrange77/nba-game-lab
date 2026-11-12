"""Export the recorded two-round demo as a self-contained, accessible SVG.

The topology is validated before drawing; no nodes, timings or statuses are
invented. The larger, compact layout is intentionally a diagram export rather
than a reproduction of the application's screenshot.
"""
import argparse
from html import escape
import json
from pathlib import Path


def export(source, target):
    record = json.loads(Path(source).read_text())
    flow = record['research_flow']
    nodes = flow['nodes']
    assert flow['status'] == 'completed' and all(n['status'] == 'completed' for n in nodes)
    lead, = [n for n in nodes if n['role'] == 'lead']
    first = [n for n in nodes if n['role'] == 'researcher' and n['round'] == 1]
    follow, = [n for n in nodes if n['role'] == 'researcher' and n['round'] == 2]
    review1, = [n for n in nodes if n['role'] == 'review' and n['round'] == 1]
    review2, = [n for n in nodes if n['role'] == 'review' and n['round'] == 2]
    writer, = [n for n in nodes if n['role'] == 'writer']
    assert len(nodes) == 9 and len(first) == 4
    assert not lead['depends_on']
    assert all(n['depends_on'] == [lead['id']] for n in first)
    assert set(review1['depends_on']) == {n['id'] for n in first}
    assert follow['depends_on'] == [review1['id']]
    assert review2['depends_on'] == [follow['id']]
    assert writer['depends_on'] == [review2['id']]
    width, height = 1240, 680
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title description">',
             '<title id="title">Recorded multi-agent research: four parallel Researchers and one targeted follow-up</title>',
             '<desc id="description">'+escape(record['question'])+' The diagram is a vector export of actual completed execution, not a screenshot.</desc>',
             '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M 1 1 L 9 5 L 1 9" fill="none" stroke="#849bb8" stroke-width="1.8"/></marker></defs>',
             '<rect width="1240" height="680" rx="18" fill="#0d1524"/>',
             '<g font-family="Arial, Helvetica, sans-serif">']

    def text(x, y, value, size=20, fill='#edf4ff', weight='400', anchor='start'):
        parts.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{fill}" font-weight="{weight}" text-anchor="{anchor}">{escape(str(value))}</text>')

    def edge(path, ids):
        parts.append('<path data-edge="'+escape(ids,quote=True)+'" d="'+path+'" fill="none" stroke="#849bb8" stroke-width="2.4" stroke-linecap="round" marker-end="url(#arrow)"/>')

    def card(node, x, y, h=112, accent='#59c9a5', fill='#162337'):
        parts.append(f'<g data-node-id="{escape(node["id"],quote=True)}">')
        parts.append(f'<rect x="{x}" y="{y}" width="276" height="{h}" rx="13" fill="{fill}" stroke="{accent}" stroke-opacity=".65" stroke-width="1.6"/>')
        parts.append(f'<circle cx="{x+22}" cy="{y+27}" r="8" fill="{accent}" fill-opacity=".16"/>')
        parts.append(f'<path d="M {x+18} {y+27} l 3 3 l 5 -6" fill="none" stroke="{accent}" stroke-width="1.7"/>')
        role = ('ROUND '+str(node['round'])) if node['role'] == 'researcher' else node['role'].upper()
        text(x+39,y+32,role,14,accent,'700')
        text(x+18,y+62,node['label'],22,weight='700')
        duration = max(0,node['ended_ms']-node['started_ms'])/1000
        timing = '<1s' if duration < 1 else f'{duration:.1f}s'
        status = ('Round '+str(node['round'])+' · ') if node['role']=='review' else ''
        text(x+18,y+89,status+'Completed · '+timing,17,'#b5c6dc')
        parts.append('</g>')

    text(32,42,'Cross-era scoring research',28,weight='700')
    text(32,73,'Jordan 1990-91 vs James 2014-15 · recorded execution',19,'#b5c6dc')
    text(1208,42,f"{flow['peak_parallel']} concurrent Researchers",20,'#7de0be','700','end')
    text(1208,73,f"2 rounds · 5 Researcher starts · {flow['elapsed_ms']/1000:.1f}s",18,'#b5c6dc',anchor='end')
    positions = [32,332,632,932]
    # The top fan-out and join are drawn from the validated dependency set.
    for x,node in zip(positions,first):
        center=x+138
        edge(f'M 620 214 V 226 H {center} V 260',lead['id']+':'+node['id'])
        edge(f'M {center} 372 V 410 H 170 V 464',node['id']+':'+review1['id'])
    chain=[review1,follow,review2,writer]
    for x,left,right in zip(positions,chain,chain[1:]):
        edge(f'M {x+276} 520 H {x+300}',left['id']+':'+right['id'])
    text(32,211,'ROUND 1 · INDEPENDENT RESEARCH IN PARALLEL',15,'#9cacc4','700')
    text(332,445,'EVIDENCE REVIEW → TARGETED FOLLOW-UP → SUMMARY',15,'#9cacc4','700')
    card(lead,482,102)
    for x,node in zip(positions,first):card(node,x,260)
    for x,node in zip(positions,chain):
        color='#f2c26c' if node['id']==follow['id'] else '#a5b5ff' if node['role']=='writer' else '#59c9a5'
        fill='#30291e' if node['id']==follow['id'] else '#222c49' if node['role']=='writer' else '#162337'
        card(node,x,464,accent=color,fill=fill)
    text(32,615,'Finding: sparse helper appearances triggered one matched investigation; original samples were retained.',18,'#c6d5e8')
    text(32,650,'Vector export of the actual execution record · not an application screenshot',16,'#91a5c0')
    parts.extend(['</g>','</svg>'])
    Path(target).write_text('\n'.join(parts)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('target')
    args=parser.parse_args()
    export(args.source,args.target)
