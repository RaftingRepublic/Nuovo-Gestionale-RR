/**
 * Settings Store — Pannello di Controllo Variabili Logistiche.
 *
 * Gestisce il fetch, la modifica locale e il salvataggio massivo
 * delle impostazioni di sistema (capienze mezzi, tempi logistici).
 * Legge/scrive su SQLite via FastAPI /api/v1/logistics/settings.
 */

import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useSettingsStore = defineStore('settings', {
  state: () => ({
    /** @type {Array<{key: string, value: string, category: string, description: string}>} */
    settings: [],
    loading: false,
    error: null,
  }),

  getters: {
    /**
     * Raggruppa le settings per category → { "Capienze Mezzi": [...], "Tempi Base (min)": [...] }
     */
    groupedByCategory: (state) => {
      const groups = {}
      for (const s of state.settings) {
        const cat = s.category || 'Generale'
        if (!groups[cat]) groups[cat] = []
        groups[cat].push(s)
      }
      return groups
    },

    /**
     * Accesso rapido per chiave: getSetting('van_total_seats') → "9"
     */
    getSetting: (state) => (key) => {
      const s = state.settings.find(x => x.key === key)
      return s ? s.value : null
    },

    /**
     * Versione numerica: getSettingNum('van_total_seats') → 9
     */
    getSettingNum: (state) => (key) => {
      const s = state.settings.find(x => x.key === key)
      return s ? parseFloat(s.value) : 0
    },

    /**
     * Categorie ordinate per visualizzazione UI coerente.
     */
    categoryOrder: () => [
      'Capienze Mezzi',
      'Tempi Base (min)',
      'Tempi Tratto A (min)',
      'Tempi Tratto B (min)',
    ],
  },

  actions: {
    /**
     * Carica tutte le impostazioni dal backend.
     */
    async fetchSettings() {
      this.loading = true
      this.error = null
      try {
        const { data } = await api.get('/logistics/settings')
        this.settings = data
      } catch (err) {
        console.error('[SettingsStore] Errore fetch:', err)
        this.error = 'Impossibile caricare le impostazioni.'
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Salva in batch tutte le settings modificate.
     * @returns {Promise<void>}
     */
    async saveAllSettings() {
      this.loading = true
      this.error = null
      try {
        const payload = {
          settings: this.settings.map(s => ({
            key: s.key,
            value: String(s.value),
          })),
        }
        const { data } = await api.put('/logistics/settings/bulk', payload)
        // Aggiorna lo stato locale con i valori confermati dal backend
        for (const updated of data) {
          const idx = this.settings.findIndex(s => s.key === updated.key)
          if (idx !== -1) {
            this.settings[idx].value = updated.value
          }
        }
      } catch (err) {
        console.error('[SettingsStore] Errore salvataggio:', err)
        this.error = 'Errore durante il salvataggio.'
        throw err
      } finally {
        this.loading = false
      }
    },

    /**
     * Aggiorna un singolo setting nello stato locale (binding bidirezionale).
     * NON salva automaticamente — l'utente deve premere "Salva".
     */
    updateLocalValue(key, newValue) {
      const s = this.settings.find(x => x.key === key)
      if (s) s.value = String(newValue)
    },
  },
})
