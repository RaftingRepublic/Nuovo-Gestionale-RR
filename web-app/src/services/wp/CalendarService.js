/**
 * CalendarService — API Blueprint §2: Calendario
 */
import { wpApi } from 'src/boot/axios'

export const CalendarService = {
  /** GET /wp-json/v2/calendar */
  getAll() {
    return wpApi.get('/v2/calendar')
  },

  /** GET /wp-json/v2/calendar/future */
  getFuture() {
    return wpApi.get('/v2/calendar/future')
  },
}
