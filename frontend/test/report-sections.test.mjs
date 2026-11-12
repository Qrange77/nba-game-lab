import { test } from 'node:test'
import assert from 'node:assert/strict'
import { reportSections } from '../src/reportSections.ts'

test('new reports keep the answer, key evidence and qualifications visible', () => {
  const source = '# Scoring Comparison\n\n## Answer\nDirk leads.\n## Key evidence\nPPG: 25.73.\n## Comparable evidence\nA complete table.\n## What changes the interpretation?\nA real counterexample.\n## Scope and methods\nOriginal formulas.'
  const sections = reportSections(source)
  const visible = sections.filter(s => !s.collapsed).map(s => s.source).join('\n')
  assert.match(visible, /Dirk leads|25.73|A real counterexample/)
  assert.doesNotMatch(visible, /complete table|Original formulas/)
  assert.equal(sections.filter(s => s.collapsed).length, 2)
  assert.match(sections.map(s => s.source).join('\n'), /complete table|Original formulas/)
})

test('legacy history and clarification replies are not reformatted', () => {
  for (const source of ['Please choose two equal windows.', '# Scoring Claim Review\n\n## Comparison contract\nHistorical answer.']) {
    assert.deepEqual(reportSections(source), [{ title: '', source, collapsed: false }])
  }
})

test('only known detail sections collapse and nested headings stay attached', () => {
  const sections = reportSections('# Scoring Claim Review\n## Answer\nResult.\n## Sensitivity and counterevidence\nChecks.\n### Phase changes\nNumbers.\n## An unfamiliar section\nVisible.')
  assert.equal(sections.find(s => s.title === 'All metric checks and phase changes').collapsed, true)
  assert.match(sections.find(s => s.collapsed).source, /### Phase changes\nNumbers/)
  assert.equal(sections.at(-1).collapsed, false)
})

test('heading-like content in a fenced example cannot create a section', () => {
  const sections = reportSections('# Scoring Comparison\n## Answer\n```text\n## Scope and methods\n```\nStill visible.')
  assert.equal(sections.filter(s => s.collapsed).length, 0)
})

 test('evidence-driven follow-up stays visible before detailed tables', () => {
  const sections = reportSections('# Scoring Claim Review\n## Answer\nConditional.\n## Key evidence\nVerified figures.\n## Why we investigated further\nSparse sample; matched baseline checked.\n## Comparable evidence\nDetails.');
  assert.equal(sections.find(s => s.title === 'Why we investigated further').collapsed, false);
  assert.equal(sections.find(s => s.title === 'Full comparison table').collapsed, true);
});

test('impact reports preserve conclusions and follow-up while folding detailed evidence', () => {
  const sections = reportSections('# On-Court Impact Review\n## Answer\nA supported position.\n## Why we investigated further\nA real gap.\n## Evidence by dimension\nDetailed numbers.\n## Team on/off evidence\nSeparate stints.')
  assert.equal(sections.filter(s => s.collapsed).length, 2)
  const visible = sections.filter(s => !s.collapsed).map(s => s.source).join('\n')
  assert.match(visible, /supported position/)
  assert.match(visible, /real gap/)
  assert.doesNotMatch(visible, /Detailed numbers|Separate stints/)
})
