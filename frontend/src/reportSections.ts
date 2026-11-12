export interface ReportSection { title: string; source: string; collapsed: boolean }

const detailTitles: Record<string, string> = {
  'Dimension findings': 'Dimension-level findings',
  'Evidence by dimension': 'Detailed contribution evidence',
  'Team on/off evidence': 'Team on/off evidence',
  'Comparable evidence': 'Full comparison table',
  'Sensitivity and counterevidence': 'All metric checks and phase changes',
  'Core helpers and rotation context': 'Supporting-cast evidence',
  'Finals opposition within the selected scope': 'Finals-opponent evidence',
  'Coverage and limits': 'Coverage and limitations',
  'Scope and methods': 'Scope, formulas and methods',
}

export function reportSections(source: string): ReportSection[] {
  // Only the new server report opts into folding. Legacy history and ordinary
  // clarification replies retain their original presentation.
  if (!/^# (?:Scoring (?:Claim Review|Comparison)|On-Court Impact Review)\n/.test(source) || !/^## Answer$/m.test(source)) {
    return [{ title: '', source, collapsed: false }]
  }
  const sections: ReportSection[] = []
  let heading = ''
  let lines: string[] = []
  let fenced = false
  function append() {
    if (!lines.length) return
    sections.push({ title: detailTitles[heading] || heading, source: lines.join('\n'), collapsed: heading in detailTitles })
  }
  for (const line of source.split('\n')) {
    if (/^```|^~~~/.test(line)) fenced = !fenced
    const match = !fenced && /^## (.+)$/.exec(line)
    if (match) { append(); heading = match[1]; lines = [] }
    lines.push(line)
  }
  append()
  return sections
}
