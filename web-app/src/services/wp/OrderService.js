/**
 * OrderService — API Blueprint §6: Ordini
 */
import { wpApi } from 'src/boot/axios'

export const OrderService = {
  /** GET /wp-json/v2/orders/?ride_date=...&ride_code=...&ride_time=... */
  getByRide(rideDate, rideCode, rideTime) {
    return wpApi.get('/v2/orders/', {
      params: { ride_date: rideDate, ride_code: rideCode, ride_time: rideTime },
    })
  },

  /** POST /wp-json/v2/orders/ */
  create(payload) {
    return wpApi.post('/v2/orders/', payload)
  },

  /** PATCH /wp-json/v2/orders/{id} */
  update(id, payload) {
    return wpApi.patch(`/v2/orders/${id}`, payload)
  },
}
