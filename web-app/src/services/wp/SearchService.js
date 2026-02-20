/**
 * SearchService — API Blueprint §10: Ricerca Ordini
 */
import { wpApi } from 'src/boot/axios'

export const SearchService = {
  /** GET /wp-json/v2/find/?name=...&surname=... */
  findOrders(name, surname) {
    return wpApi.get('/v2/find/', { params: { name, surname } })
  },
}
