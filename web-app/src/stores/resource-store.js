import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'

export const useResourceStore = defineStore('resource', {
  state: () => ({
    staffList: [],
    fleetList: [],
    activityRules: [],
    dailySchedule: [],
    currentResourceRules: [], // NUOVO: Regole della risorsa selezionata (per calendario)
    loading: false,
    selectedStaffId: null
  }),

  getters: {
    activeStaff: (state) => state.staffList.filter(s => s.is_active),
    selectedStaffMember: (state) => state.staffList.find(s => s.id === state.selectedStaffId),
    selectedResource: (state) => {
      return state.staffList.find(s => s.id === state.selectedStaffId) ||
        state.fleetList.find(f => f.id === state.selectedStaffId)
    },
    rafts: (state) => state.fleetList.filter(f => f.type === 'RAFT'),
    vans: (state) => state.fleetList.filter(f => f.type === 'VAN'),
    trailers: (state) => state.fleetList.filter(f => f.type === 'TRAILER')
  },

  actions: {
    // --- STAFF ---
    async fetchStaff() {
      try { this.staffList = (await api.get('/resources/staff')).data }
      catch (e) { console.error(e) }
    },
    async addStaff(payload) {
      const res = await api.post('/resources/staff', payload)
      this.staffList.push(res.data)
    },
    async deleteStaff(id) {
      await api.delete(`/resources/staff/${id}`)
      this.staffList = this.staffList.filter(s => s.id !== id)
      if (this.selectedStaffId === id) this.selectedStaffId = null
    },

    // --- FLEET ---
    async fetchFleet() {
      try { this.fleetList = (await api.get('/resources/fleet')).data }
      catch (e) { console.error(e) }
    },
    async addFleet(payload) {
      const res = await api.post('/resources/fleet', payload)
      this.fleetList.push(res.data)
    },
    async deleteFleet(id) {
      await api.delete(`/resources/fleet/${id}`)
      this.fleetList = this.fleetList.filter(f => f.id !== id)
      if (this.selectedStaffId === id) this.selectedStaffId = null
    },

    // --- ACTIVITY ---
    async fetchActivityRules() {
      try { this.activityRules = (await api.get('/resources/activity-rules')).data }
      catch (e) { console.error(e) }
    },
    async addActivityRule(payload) {
      const res = await api.post('/resources/activity-rules', payload)
      this.activityRules.push(res.data)
    },
    async deleteActivityRule(id) {
      await api.delete(`/resources/activity-rules/${id}`)
      this.activityRules = this.activityRules.filter(r => r.id !== id)
    },
    async fetchDailySchedule(date) {
      this.loading = true
      try { this.dailySchedule = (await api.get('/resources/daily-schedule', { params: { date } })).data }
      catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async fetchMonthOverview(year, month, detailed = false) {
      try { return (await api.get('/resources/month-overview', { params: { year, month, detailed } })).data }
      catch (e) { console.error(e); return [] }
    },

    // --- AVAILABILITY ---
    async fetchResourceRules(resourceId) {
      try { this.currentResourceRules = (await api.get(`/resources/availability/${resourceId}`)).data }
      catch (e) { console.error(e) }
    },
    async addAvailability(payload) {
      this.loading = true
      try {
        await api.post('/resources/availability', payload)
        // Aggiorna subito le regole locali per vederle sul calendario
        await this.fetchResourceRules(payload.staff_id)
      }
      finally { this.loading = false }
    },

    selectStaff(id) { this.selectedStaffId = id }
  }
})