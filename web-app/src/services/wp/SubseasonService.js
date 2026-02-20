/**
 * SubseasonService — API Blueprint §5: Sottoperiodi
 */
import { wpApi } from 'src/boot/axios'

export const SubseasonService = {
  /** GET /wp-json/v2/subseason/?ride_id=... */
  getByRide(rideId) {
    return wpApi.get('/v2/subseason/', { params: { ride_id: rideId } })
  },

  /** POST /wp-json/v2/subseason/ */
  create(payload) {
    return wpApi.post('/v2/subseason/', payload)
  },

  /** DELETE /wp-json/v2/subseason/{id} */
  delete(id) {
    return wpApi.delete(`/v2/subseason/${id}`)
  },
}
