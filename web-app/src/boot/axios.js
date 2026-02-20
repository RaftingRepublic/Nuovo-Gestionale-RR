import { boot } from 'quasar/wrappers'
import axios from 'axios'

// ─────────────────────────────────────────────────────────
// CANALE 1 — Backend Python locale (invariato)
// Usato dagli store esistenti (resource-store, reservation-store, ecc.)
// ─────────────────────────────────────────────────────────
const api = axios.create({ baseURL: '/api/v1' })

// ─────────────────────────────────────────────────────────
// CANALE 2 — Backend WordPress (NUOVO)
// Usa la Base URL dal file .env, punta a /wp-json
// ─────────────────────────────────────────────────────────
const wpApi = axios.create({
  baseURL: import.meta.env.VITE_WP_BASE_URL + '/wp-json',
  headers: { 'Content-Type': 'application/json' },
})

// ─────────────────────────────────────────────────────────
// INTERCEPTOR DI RICHIESTA — Il "Postino Sicuro"
// Prima che ogni chiamata wpApi parta verso WordPress,
// appicchiamo di nascosto il Token JWT nell'header.
// ─────────────────────────────────────────────────────────
const TOKEN_KEY = 'rr_auth_token'

wpApi.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ─────────────────────────────────────────────────────────
// INTERCEPTOR DI RISPOSTA — La "Guardia in Uscita"
// Se WordPress risponde 401/403 (token scaduto o invalido),
// cancelliamo il token e redirigiamo al login.
// ─────────────────────────────────────────────────────────
wpApi.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && [401, 403].includes(error.response.status)) {
      localStorage.removeItem(TOKEN_KEY)
      // Il redirect al login verrà gestito dal router guard
      // o dal componente che cattura l'errore
      console.warn('[wpApi] Sessione scaduta — token rimosso.')
    }
    return Promise.reject(error)
  },
)

export default boot(({ app }) => {
  // Rende le istanze disponibili globalmente (template Options API)
  app.config.globalProperties.$axios = axios
  app.config.globalProperties.$api = api
  app.config.globalProperties.$wpApi = wpApi
})

export { api, wpApi }
