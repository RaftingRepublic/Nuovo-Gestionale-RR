/**
 * AvailabilityService — API Blueprint §9: Disponibilità
 */
import { wpApi } from 'src/boot/axios'

export const AvailabilityService = {
  /** GET /wp-json/v2/availability/?ride_date=...&ride_code=...&ride_time=... */
  get(rideDate, rideCode, rideTime) {
    return wpApi.get('/v2/availability/', {
      params: { ride_date: rideDate, ride_code: rideCode, ride_time: rideTime },
    })
  },

  /** POST /wp-json/v2/availability/ */
  save(payload) {
    return wpApi.post('/v2/availability/', payload)
  },
}
