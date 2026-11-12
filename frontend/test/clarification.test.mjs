import { test } from 'node:test'
import assert from 'node:assert/strict'
import { clarificationPrompt, windowReply } from '../src/clarification.ts'

function turn(overrides = {}) {
  return { response: 'Choose careers or equal-length season windows.',
    research_flow: { status: 'clarification' },
    selected_players: [{ name: 'Michael Jordan' }, { name: 'LeBron James' }],
    tool_calls: [{ name: 'confirm_scoring_contract', result: JSON.stringify({ action: 'clarify', clarification_kind: 'period', cutoff: 2025 }) }], ...overrides }
}

test('structured clarification shows period choices only with two confirmed players', () => {
  assert.equal(clarificationPrompt(turn()).kind, 'period')
  assert.equal(clarificationPrompt(turn({ selected_players: [] })).kind, 'custom')
})

test('completed reports, identity questions and failed replies cannot produce scope actions', () => {
  for (const changes of [{ research_flow: { status: 'completed' } }, { failed: true }, { player_clarifications: [{ query: 'Jordan' }] }, { tool_calls: [] }])
    assert.equal(clarificationPrompt(turn(changes)), null)
})

test('legacy period questions remain clickable, other old prompts stay free text', () => {
  const tool_calls = [{ name: 'confirm_scoring_contract', result: { action: 'clarify', cutoff: 2025 } }]
  assert.equal(clarificationPrompt(turn({ tool_calls, response: 'Would you like career scoring or equal-length season windows?' })).kind, 'period')
  assert.equal(clarificationPrompt(turn({ tool_calls, response: 'Which cutoff did you mean?' })).kind, 'custom')
})

test('malformed metadata falls back to the original readable reply', () => {
  assert.equal(clarificationPrompt(turn({ tool_calls: [{ name: 'confirm_scoring_contract', result: '{' }] })), null)
})

test('equal windows create a plain user clarification with exact identities and seasons', () => {
  assert.deepEqual(windowReply(['Michael Jordan', 'LeBron James'], ['1990', '1990', '2014', '2014'], 2025), {
    message: 'Use Michael Jordan in 1990-91 through 1990-91, and LeBron James in 2014-15 through 2014-15.', error: '' })
})

test('invalid, incomplete, unequal and unsupported windows cannot submit', () => {
  for (const years of [['', '', '', ''], ['1990', '1992', '2014', '2014'], ['1992', '1990', '2014', '2014'], ['1983', '1983', '2014', '2014'], ['2026', '2026', '2014', '2014'], ['1990.5', '1990', '2014', '2014']]) {
    const result = windowReply(['Alpha', 'Beta'], years, 2025)
    assert.equal(result.message, '')
    assert.ok(result.error)
  }
})
