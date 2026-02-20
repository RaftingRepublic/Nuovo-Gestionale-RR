/**
 * AuthService — Chiamate di autenticazione verso WordPress JWT.
 *
 * Questo service è usato internamente dall'auth-store.
 * Per il login, usare sempre useAuthStore().login() dai componenti.
 */
import { wpApi } from 'src/boot/axios'

export const AuthService = {
  /**
   * POST /wp-json/jwt-auth/v1/token
   * @param {string} username
   * @param {string} password
   * @returns {Promise<{token: string, user_display_name: string, roles: string}>}
   */
  login(username, password) {
    return wpApi.post('/jwt-auth/v1/token', { username, password })
  },
}
