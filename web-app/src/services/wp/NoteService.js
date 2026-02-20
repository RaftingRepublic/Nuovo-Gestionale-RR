/**
 * NoteService — API Blueprint §7: Note
 */
import { wpApi } from 'src/boot/axios'

export const NoteService = {
  /** GET /wp-json/v2/notes */
  getAll() {
    return wpApi.get('/v2/notes')
  },

  /** GET /wp-json/v2/notes/future */
  getFuture() {
    return wpApi.get('/v2/notes/future')
  },

  /** POST /wp-json/v2/notes/ */
  create(payload) {
    return wpApi.post('/v2/notes/', payload)
  },

  /** PATCH /wp-json/v2/notes/{id} */
  update(id, payload) {
    return wpApi.patch(`/v2/notes/${id}`, payload)
  },

  /** DELETE /wp-json/v2/notes/{id} */
  delete(id) {
    return wpApi.delete(`/v2/notes/${id}`)
  },
}
