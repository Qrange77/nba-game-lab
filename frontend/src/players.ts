import type { PlayerChoice } from './types'

export function playerYears(player: PlayerChoice): string {
  return player.from_year && player.to_year
    ? `${player.from_year}–${player.active ? 'present' : Number(player.to_year) + 1}`
    : 'Playing years unavailable'
}
