import { test } from 'node:test'
import assert from 'node:assert/strict'
import { layoutFlow, acceptFlow, interruptFlow, NODE_HEIGHT } from '../src/researchFlow.ts'

const node = (id, parents = [], status = 'completed', role = 'researcher') => ({id, label:id, depends_on:parents, status, role, agent:id, round:1, started_ms:0, ended_ms:100, tool_ids:[], description:'Task', summary:''})
const flow = nodes => ({version:1, status:'running', elapsed_ms:100, peak_parallel:2, nodes})

test('initial Lead renders alone with no speculative future nodes', () => {
  const graph = layoutFlow([node('lead', [], 'running', 'lead')])
  assert.equal(graph.nodes.length, 1); assert.equal(graph.edges.length, 0)
})

test('four researchers share a column with no overlaps and converge on review', () => {
  const graph = layoutFlow([node('lead'), ...['a','b','c','d'].map(id => node(id,['lead'])), node('review',['a','b','c','d']), node('writer',['review'])])
  const workers = graph.nodes.filter(n => ['a','b','c','d'].includes(n.id))
  assert.equal(new Set(workers.map(n => n.x)).size,1)
  for (let i=1;i<workers.length;i++) assert.ok(workers[i].y >= workers[i-1].y+NODE_HEIGHT)
  assert.equal(graph.edges.length,9)
  assert.ok(graph.nodes.find(n => n.id==='review').x > workers[0].x)
})

test('second-round work follows the first review without repeating completed branches', () => {
  const graph = layoutFlow([node('lead'),node('a',['lead'],'partial'),node('b',['lead']),node('r1',['a','b']),node('c',['r1']),node('r2',['c']),node('writer',['r2'])])
  assert.equal(graph.nodes.find(n=>n.id==='c').column,3)
  assert.equal(graph.nodes.find(n=>n.id==='writer').column,5)
  assert.equal(graph.nodes.filter(n=>n.id==='b').length,1)
  assert.equal(graph.nodes.find(n=>n.id==='a').status,'partial')
})

test('out-of-order stream snapshots cannot regress visible execution', () => {
  const newer={...flow([node('lead'),node('a',['lead'])]),version:5}
  assert.equal(acceptFlow(newer,flow([node('lead')])),newer)
})

test('disconnect preserves successful work and stops claiming active execution', () => {
  const source=flow([node('lead'),node('a',['lead'],'running'),node('b',['lead'],'queued')])
  const result=interruptFlow(source)
  assert.equal(result.status,'interrupted')
  assert.deepEqual(result.nodes.map(n=>n.status),['completed','interrupted','cancelled'])
  assert.equal(source.nodes[1].status,'running')
  assert.equal(interruptFlow({...source,status:'completed'}).status,'completed')
})
