import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useResourceStore = defineStore('resource', {
  state: () => ({
    staffList: [],
    fleetList: [],
    resourceExceptions: [],  // Eccezioni della risorsa selezionata
    activityRules: [],
    dailySchedule: [],
    loading: false,
    selectedResourceId: null
  }),

  getters: {
    activeStaff: (state) => state.staffList.filter(s => s.is_active),
    staffFisso: (state) => state.staffList.filter(s => s.contract_type === 'FISSO'),
    staffExtra: (state) => state.staffList.filter(s => s.contract_type === 'EXTRA'),
    selectedResource: (state) => {
      return state.staffList.find(s => s.id === state.selectedResourceId) ||
        state.fleetList.find(f => f.id === state.selectedResourceId)
    },
    // Determina se la risorsa selezionata è Staff o Fleet
    selectedResourceType: (state) => {
      if (state.staffList.find(s => s.id === state.selectedResourceId)) return 'STAFF'
      if (state.fleetList.find(f => f.id === state.selectedResourceId)) return 'FLEET'
      return null
    },
    // Determina se la risorsa è "Extra" (turni) o "Fissa" (assenze)
    selectedIsExtra: (state) => {
      const staff = state.staffList.find(s => s.id === state.selectedResourceId)
      return staff ? staff.contract_type === 'EXTRA' : false
    },
    rafts: (state) => state.fleetList.filter(f => f.category === 'RAFT'),
    vans: (state) => state.fleetList.filter(f => f.category === 'VAN'),
  },

  actions: {
    // --- STAFF ---
    async fetchStaff() {
      try { this.staffList = (await api.get('/logistics/staff')).data }
      catch (e) { console.error(e) }
    },
    async addStaff(payload) {
      const res = await api.post('/logistics/staff', payload)
      this.staffList.push(res.data)
    },
    async deleteStaff(id) {
      await api.delete(`/logistics/staff/${id}`)
      this.staffList = this.staffList.filter(s => s.id !== id)
      if (this.selectedResourceId === id) this.selectedResourceId = null
    },
    async updateStaff(staffId, payload) {
      const res = await api.patch(`/logistics/staff/${staffId}`, payload)
      const idx = this.staffList.findIndex(s => s.id === staffId)
      if (idx !== -1) this.staffList[idx] = res.data
    },

    // --- FLEET ---
    async fetchFleet() {
      try { this.fleetList = (await api.get('/logistics/fleet')).data }
      catch (e) { console.error(e) }
    },
    async addFleet(payload) {
      const res = await api.post('/logistics/fleet', payload)
      this.fleetList.push(res.data)
    },
    async deleteFleet(id) {
      await api.delete(`/logistics/fleet/${id}`)
      this.fleetList = this.fleetList.filter(f => f.id !== id)
      if (this.selectedResourceId === id) this.selectedResourceId = null
    },

    // --- RESOURCE EXCEPTIONS (Diario Unificato) ---
    async fetchResourceExceptions(resourceId) {
      try {
        this.resourceExceptions = (await api.get('/logistics/resource-exceptions', {
          params: { resource_id: resourceId }
        })).data
      }
      catch (e) { console.error(e); this.resourceExceptions = [] }
    },

    async saveException(payload) {
      this.loading = true
      try {
        await api.post('/logistics/resource-exceptions', payload)
        await this.fetchResourceExceptions(payload.resource_id)
      }
      finally { this.loading = false }
    },

    async deleteException(exceptionId, resourceId) {
      await api.delete(`/logistics/resource-exceptions/${exceptionId}`)
      await this.fetchResourceExceptions(resourceId)
    },

    // --- SETTINGS ---
    async fetchSettings() {
      try { return (await api.get('/logistics/settings')).data }
      catch (e) { console.error(e); return [] }
    },
    async updateSetting(key, value) {
      await api.patch(`/logistics/settings/${key}`, { value })
    },

    // --- ACTIVITY RULES ---
    async fetchActivityRules() {
      try { this.activityRules = (await api.get('/resources/activity-rules')).data }
      catch (e) { console.error('fetchActivityRules error:', e); this.activityRules = [] }
    },
    async addActivityRule(payload) {
      const res = await api.post('/resources/activity-rules', payload)
      this.activityRules.push(res.data)
    },
    async deleteActivityRule(id) {
      await api.delete(`/resources/activity-rules/${id}`)
      this.activityRules = this.activityRules.filter(r => r.id !== id)
    },

    // --- DAILY SCHEDULE (Calendar) ---
    async fetchDailySchedule(date) {
      this.loading = true
      try {
        const res = await api.get('/calendar/daily-rides', { params: { date } })
        this.dailySchedule = res.data.map(ride => ({
          id: ride.id,
          time: ride.ride_time,
          activity_type: ride.activity_name,
          activity_id: ride.activity_id,
          color_hex: ride.color_hex,
          status: ride.status,
          is_overridden: ride.is_overridden,
          notes: ride.notes,
          booked_pax: ride.booked_pax,
          total_capacity: ride.total_capacity || 0,
          arr_bonus_seats: ride.arr_bonus_seats || 0,
          remaining_seats: ride.remaining_seats || 0,
          engine_status: ride.engine_status || 'VERDE',
          cap_rafts_pax: ride.total_capacity || 0,
          cap_guides_pax: ride.total_capacity || 0,
          avail_guides: '—',
          avail_rafts: '—',
          avail_vans: '—',
          status_desc: _engineStatusDesc(ride.engine_status),
        }))
      } catch (e) { console.error('fetchDailySchedule error:', e) }
      finally { this.loading = false }
    },

    async fetchMonthOverview(year, month) {
      try {
        const startDate = `${year}-${String(month).padStart(2, '0')}-01`
        const lastDay = new Date(year, month, 0).getDate()
        const endDate = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

        // Cruscotto Operativo: ritorna solo giornate con prenotazioni reali
        const res = await api.get('/calendar/daily-schedule', {
          params: { start_date: startDate, end_date: endDate }
        })

        // Indicizza per data per lookup rapido
        const byDate = {}
        for (const day of res.data) {
          byDate[day.date] = day
        }

        // Genera griglia completa del mese (giorni senza dati = celle bianche)
        const days = []
        for (let d = 1; d <= lastDay; d++) {
          const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
          const apiDay = byDate[dateStr]
          days.push({
            date: dateStr,
            booked_rides: apiDay ? apiDay.booked_rides : [],
            staff_count: apiDay ? apiDay.staff_count : 0,
          })
        }
        return days
      } catch (e) { console.error('fetchMonthOverview error:', e); return [] }
    },

    selectResource(id) { this.selectedResourceId = id }
  }
})

function _engineStatusDesc(engineStatus) {
  if (engineStatus === 'ROSSO') return 'Pieno / Chiuso'
  if (engineStatus === 'GIALLO') return 'Quasi Pieno'
  return 'Disponibile'
}
