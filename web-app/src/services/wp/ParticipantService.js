/**
 * ParticipantService — API Blueprint §8: Partecipanti
 */
import { wpApi } from 'src/boot/axios'

export const ParticipantService = {
  /** GET /wp-json/v2/participants/{orderId} */
  getByOrder(orderId) {
    return wpApi.get(`/v2/participants/${orderId}`)
  },

  /** GET /wp-json/v2/participants?date=... */
  getByDate(date) {
    return wpApi.get('/v2/participants', { params: { date } })
  },

  /** POST /wp-json/v2/participants/ */
  create(payload) {
    return wpApi.post('/v2/participants/', payload)
  },

  /** PATCH /wp-json/v2/participants/{id} */
  update(id, payload) {
    return wpApi.patch(`/v2/participants/${id}`, payload)
  },

  /** DELETE /wp-json/v2/participants/{id} */
  delete(id) {
    return wpApi.delete(`/v2/participants/${id}`)
  },
}
