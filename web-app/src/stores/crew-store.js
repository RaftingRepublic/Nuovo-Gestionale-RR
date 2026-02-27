/**
 * crew-store.js — Nastro Trasportatore Busta Stagna (Fase 7.D — Swap & Replace)
 *
 * Store Pinia dedicato al Crew Builder.
 * Comunica con il backend FastAPI via Axios (api instance dal boot).
 * Nessun contatto diretto con Supabase — tutto passa dal router crew.py.
 *
 * DOGMA 10 (Tetris Umano): i passeggeri non sono numeri anonimi.
 * Ogni gommone ha un array groups: [{ order_id, customer_name, pax }].
 *
 * DOGMA 11 (Swap & Replace): il backend rade al suolo i vecchi record
 * e bulk-inserisce i nuovi. Il frontend manda l'array piatto direttamente.
 *
 * State:
 *   allocations — Array piatto di righe gommone. Ogni riga:
 *     { resource_id, resource_type, metadata: { guide_id, groups: [] } }
 *   isLoading, lastError, currentRideId
 *
 * Actions: loadCrew(ride_id), saveCrew(ride_id, payload), clearCrew()
 */
import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useCrewStore = defineStore('crew', {
  state: () => ({
    allocations: [],
    currentRideId: null,
    isLoading: false,
    lastError: null,
  }),

  getters: {
    boatCount: (state) => state.allocations.length,

    // Pax totali assegnati (SOMMA DERIVATA Tetris Umano)
    assignedPax: (state) => {
      let total = 0
      for (const alloc of state.allocations) {
        const groups = alloc.metadata?.groups || []
        for (const g of groups) {
          total += (g.pax || 0)
        }
      }
      return total
    },

    isEmpty: (state) => state.allocations.length === 0,
  },

  actions: {
    /**
     * Carica la Busta Stagna dal backend.
     * GET /api/v1/crew/allocations/{ride_id}
     * Il backend restituisce { ride_id, allocations: [...] }
     */
    async loadCrew(rideId) {
      if (!rideId) {
        console.warn('[CrewStore] loadCrew chiamato senza ride_id')
        return
      }

      this.isLoading = true
      this.lastError = null

      try {
        const response = await api.get('/crew/allocations/' + rideId)
        const data = response.data

        // Il backend restituisce { ride_id, allocations: [...] }
        if (data && Array.isArray(data.allocations)) {
          this.allocations = data.allocations.map(item => ({
            resource_id: item.resource_id || null,
            resource_type: item.resource_type || 'RAFT',
            metadata: {
              guide_id: item.metadata?.guide_id || null,
              groups: Array.isArray(item.metadata?.groups) ? item.metadata.groups : [],
            }
          }))
        } else {
          this.allocations = []
        }

        this.currentRideId = rideId
        console.log('[CrewStore] Busta Stagna caricata per ride', rideId, '— Gommoni:', this.allocations.length)

      } catch (err) {
        console.error('[CrewStore] Errore loadCrew:', err)
        this.lastError = err.message || 'Errore caricamento equipaggio'
        this.allocations = []
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Salva la Busta Stagna sul backend.
     * PUT /api/v1/crew/allocations/{ride_id}
     *
     * Il backend accetta direttamente l'array di CrewAllocationItem.
     * Tecnica Swap & Replace: DELETE vecchi + bulk INSERT nuovi.
     */
    async saveCrew(rideId, payload) {
      if (!rideId) {
        console.warn('[CrewStore] saveCrew chiamato senza ride_id')
        return false
      }

      this.isLoading = true
      this.lastError = null

      try {
        // Invia l'array piatto direttamente come body
        const dataToSend = payload || this.allocations
        const response = await api.put('/crew/allocations/' + rideId, dataToSend)
        const data = response.data

        this.currentRideId = rideId
        console.log('[CrewStore] Busta Stagna salvata per ride', rideId, '— Count:', data?.count || 0)
        return true

      } catch (err) {
        console.error('[CrewStore] Errore saveCrew:', err)
        this.lastError = err.response?.data?.detail || err.message || 'Errore salvataggio equipaggio'
        return false
      } finally {
        this.isLoading = false
      }
    },

    /**
     * Pulisce lo store quando si chiude la modale del turno.
     */
    clearCrew() {
      this.allocations = []
      this.currentRideId = null
      this.lastError = null
    },
  },
})
