import type { ResearchFlow, FlowNode } from './types.ts'

// Vue adaptation of the dependency-column layout described by assistant-ui's
// Flow Graph: https://www.assistant-ui.com/elements/flow-graph
export const NODE_WIDTH = 128
export const NODE_HEIGHT = 72
const GAP_X = 32, GAP_Y = 18, PADDING = 16

export function layoutFlow(nodes: FlowNode[]) {
  const columns = new Map<string, number>()
  const groups: FlowNode[][] = []
  for (const node of nodes) {
    const column = node.depends_on.length ? Math.max(...node.depends_on.map(id => columns.get(id) ?? -1)) + 1 : 0
    columns.set(node.id, column)
    ;(groups[column] ??= []).push(node)
  }
  const count = Math.max(1, ...groups.map(group => group.length))
  const height = count * NODE_HEIGHT + (count - 1) * GAP_Y + 2 * PADDING
  const positioned = groups.flatMap((group, column) => group.map((node, row) => ({ ...node, column,
    x: PADDING + column * (NODE_WIDTH + GAP_X),
    y: (height - (group.length * NODE_HEIGHT + (group.length - 1) * GAP_Y)) / 2 + row * (NODE_HEIGHT + GAP_Y) })))
  const byId = new Map(positioned.map(node => [node.id, node]))
  const edges = positioned.flatMap(node => node.depends_on.flatMap(id => {
    const parent = byId.get(id)
    if (!parent) return []
    const x1 = parent.x + NODE_WIDTH, y1 = parent.y + NODE_HEIGHT / 2, x2 = node.x, y2 = node.y + NODE_HEIGHT / 2
    const bend = (x2 - x1) / 2
    return [{ id: `${id}:${node.id}`, target: node.id, status: node.status,
      path: `M ${x1} ${y1} C ${x1 + bend} ${y1}, ${x2 - bend} ${y2}, ${x2} ${y2}` }]
  }))
  return { nodes: positioned, edges, width: Math.max(1, groups.length) * NODE_WIDTH + Math.max(0, groups.length - 1) * GAP_X + 2 * PADDING, height }
}

export function acceptFlow(current: ResearchFlow | null | undefined, incoming: ResearchFlow) {
  return !current || incoming.version >= current.version ? incoming : current
}

export function interruptFlow(flow: ResearchFlow | null | undefined): ResearchFlow | null | undefined {
  if (!flow || flow.status !== 'running') return flow
  return { ...flow, status: 'interrupted', nodes: flow.nodes.map(node => node.status === 'running'
    ? { ...node, status: 'interrupted', ended_ms: flow.elapsed_ms }
    : node.status === 'queued' ? { ...node, status: 'cancelled' } : node) }
}
