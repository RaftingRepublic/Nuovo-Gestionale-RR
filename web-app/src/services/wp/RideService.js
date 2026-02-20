/**
 * RideService — API Blueprint §3-4: Attività / Stagione
 */
import { wpApi } from 'src/boot/axios'

export const RideService = {
  /** GET /wp-json/v2/rides/ */
  getAll() {
    return wpApi.get('/v2/rides/')
  },

  /** POST /wp-json/v2/season/ — Salva configurazione stagione */
  saveSeason(payload) {
    return wpApi.post('/v2/season/', payload)
  },
}
