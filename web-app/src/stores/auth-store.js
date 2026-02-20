import { defineStore } from 'pinia'
import { wpApi } from 'src/boot/axios'

const TOKEN_KEY = 'rr_auth_token'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null,
    userName: null,
    userRole: null,
  }),

  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => ['administrator', 'editor'].includes(state.userRole),
  },

  actions: {
    /**
     * Autentica l'utente contro il backend WordPress JWT.
     * Salva SOLO il token in localStorage. MAI le credenziali.
     */
    async login(username, password) {
      const res = await wpApi.post('/jwt-auth/v1/token', {
        username,
        password,
      })

      const { token, user_display_name, roles } = res.data

      // Persistenza sicura: solo il token
      localStorage.setItem(TOKEN_KEY, token)

      // State volatile (RAM) — si perde al refresh, si riotterrà al prossimo login
      this.token = token
      this.userName = user_display_name
      this.userRole = roles

      return res.data
    },

    /**
     * Disconnect: cancella ogni traccia della sessione.
     */
    logout() {
      localStorage.removeItem(TOKEN_KEY)
      this.token = null
      this.userName = null
      this.userRole = null
    },

    /**
     * Chiamato al boot dell'app: ripristina il token dal localStorage.
     * Se il token è scaduto, l'interceptor di risposta farà il logout automatico
     * alla prima chiamata 401.
     */
    loadSession() {
      const savedToken = localStorage.getItem(TOKEN_KEY)
      if (savedToken) {
        this.token = savedToken
      }
    },
  },
})
