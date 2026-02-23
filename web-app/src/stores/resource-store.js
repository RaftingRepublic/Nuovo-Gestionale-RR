import { defineStore } from 'pinia'
import { api } from 'src/boot/axios'
import { supabase } from 'src/supabase'

export const useResourceStore = defineStore('resource', {
  state: () => ({
    staffList: [],
    fleetList: [],
    resourceExceptions: [],  // Eccezioni della risorsa selezionata
    activityRules: [],
    dailySchedule: [],
    activities: [],    // Catalogo attività da Supabase
    resources: [],     // Catalogo risorse da Supabase
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
    // --- CATALOGHI SUPABASE ---
    async fetchCatalogs() {
      try {
        const { data: acts, error: errActs } = await supabase.from('activities').select('*').order('name')
        if (errActs) throw errActs
        if (acts) this.activities = acts

        const { data: res, error: errRes } = await supabase.from('resources').select('*').order('name')
        if (errRes) throw errRes
        if (res) this.resources = res
      } catch (err) {
        console.error('Errore fetch cataloghi Supabase:', err)
        throw err
      }
    },

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

    // --- DAILY SCHEDULE via Supabase ---
    async fetchDailyScheduleSupabase(dateStr) {
      this.loading = true
      try {
        const { data: rides, error } = await supabase
          .from('rides')
          .select('*, activities(*), orders(*), ride_allocations(*, resources(*))')
          .eq('date', dateStr)
          .order('time')
        if (error) throw error

        const mappedRides = (rides || []).map(ride => {
          const act = ride.activities || {}
          const orders = ride.orders || []
          const allocs = ride.ride_allocations || []
          const bookedPax = orders.reduce((sum, o) => sum + (o.actual_pax || o.pax || 0), 0)
          return {
            id: ride.id,
            time: ride.time,
            activity_type: act.name || 'Sconosciuta',
            activity_id: ride.activity_id,
            color_hex: act.color_hex || act.color || '#607d8b',
            status: ride.status || 'Disponibile',
            is_overridden: ride.is_overridden || false,
            notes: ride.notes || '',
            booked_pax: bookedPax,
            total_capacity: ride.total_capacity || act.default_capacity || 16,
            arr_bonus_seats: 0,
            remaining_seats: (ride.total_capacity || 16) - bookedPax,
            engine_status: bookedPax >= (ride.total_capacity || 16) ? 'ROSSO' : bookedPax >= (ride.total_capacity || 16) * 0.75 ? 'GIALLO' : 'VERDE',
            cap_rafts_pax: ride.total_capacity || 16,
            cap_guides_pax: ride.total_capacity || 16,
            avail_guides: '—',
            avail_rafts: '—',
            avail_vans: '—',
            status_desc: _engineStatusDesc(bookedPax >= (ride.total_capacity || 16) ? 'ROSSO' : bookedPax >= (ride.total_capacity || 16) * 0.75 ? 'GIALLO' : 'VERDE'),
            assigned_staff: ride.assigned_staff || [],
            assigned_fleet: ride.assigned_fleet || [],
            orders: orders.map(o => ({
              id: o.id,
              ride_id: o.ride_id,
              order_status: o.status || 'CONFERMATO',
              total_pax: o.pax || 1,
              _actual_pax: o.actual_pax || o.pax || 1,
              price_total: o.total_price || 0,
              paid_amount: o.paid_amount || 0,
              payment_type: o.payment_type || 'CASH',
              customer_name: o.customer_name || 'Senza nome',
              customer_surname: o.customer_surname || '',
              customer_email: o.customer_email || '',
              customer_phone: o.customer_phone || '',
              language: o.language || 'IT',
              is_exclusive_raft: o.is_exclusive_raft || false,
              notes: o.notes || '',
              discount_applied: o.discount_applied || 0,
              registrations: [],
            })),
            guides: allocs.filter(a => a && a.resources && a.resources.type === 'guide').map(a => a.resources),
            rafts: allocs.filter(a => a && a.resources && a.resources.type === 'raft').map(a => a.resources),
            vans: allocs.filter(a => a && a.resources && a.resources.type === 'van').map(a => a.resources),
            trailers: allocs.filter(a => a && a.resources && a.resources.type === 'trailer').map(a => a.resources),
            isGhost: false,
            date: dateStr,
          }
        })

        // Ghost Skeleton: genera slot vuoti per gli orari base mancanti
        // BLINDATURA: isolato in try/catch dedicato per evitare silent crash
        const baseSlots = [
          { time: '09:00', defaultTitle: 'Rafting Family' },
          { time: '10:00', defaultTitle: 'Rafting Selection' },
          { time: '11:00', defaultTitle: 'Rafting Classic' },
          { time: '13:30', defaultTitle: 'Rafting Classic' },
          { time: '14:00', defaultTitle: 'Rafting Selection' },
          { time: '15:00', defaultTitle: 'Hydrospeed Base' },
          { time: '16:00', defaultTitle: 'Rafting Family' },
        ]

        try {
          const storeActivities = Array.isArray(this.activities) ? this.activities : []
          const ghosts = []
          for (const slot of baseSlots) {
            if (!mappedRides.some(r => r && r.time && String(r.time).startsWith(slot.time))) {
              const act = storeActivities.find(a => a && a.name && String(a.name).toLowerCase() === slot.defaultTitle.toLowerCase())
              const validActId = (act && act.id) ? act.id : 'ghost-id'
              const cap = (act && act.default_capacity) ? act.default_capacity : 16

              ghosts.push({
                id: 'ghost-' + slot.time.replace(':', ''),
                time: slot.time + ':00',
                activity_type: act ? act.name : slot.defaultTitle,
                activity_name: act ? act.name : slot.defaultTitle,
                activity_id: validActId,
                title: act ? act.name : slot.defaultTitle,
                color: act ? (act.color_hex || act.color || '#e0e0e0') : '#e0e0e0',
                color_hex: act ? (act.color_hex || act.color || '#e0e0e0') : '#e0e0e0',
                status: 'Disponibile',
                is_overridden: false,
                notes: '',
                booked_pax: 0,
                total_capacity: cap,
                arr_bonus_seats: 0,
                remaining_seats: cap,
                engine_status: 'VERDE',
                status_desc: 'Disponibile',
                cap_rafts_pax: cap,
                cap_guides_pax: cap,
                avail_guides: '—',
                avail_rafts: '—',
                avail_vans: '—',
                assigned_staff: [],
                assigned_fleet: [],
                orders: [],
                guides: [],
                rafts: [],
                vans: [],
                trailers: [],
                isGhost: true,
                date: dateStr,
                capacity: { max: cap },
              })
            }
          }

          // Unisci e ordina per orario — usa splice per preservare la reattività Pinia
          const combined = [...mappedRides, ...ghosts].sort((a, b) =>
            String(a.time || '').localeCompare(String(b.time || ''))
          )
          this.dailySchedule.splice(0, this.dailySchedule.length, ...combined)
        } catch (ghostErr) {
          console.error('[GHOST GENERATION ERROR]', ghostErr)
          // Fallback: mostra almeno i turni reali dal DB senza svuotare lo schermo
          this.dailySchedule.splice(0, this.dailySchedule.length, ...mappedRides)
        }
      } catch (e) {
        console.error('[Supabase Error] fetchDailyScheduleSupabase:', e)
        this.dailySchedule.splice(0, this.dailySchedule.length)
      }
      finally { this.loading = false }
    },

    async fetchMonthOverviewSupabase(year, month) {
      try {
        const startDate = `${year}-${String(month).padStart(2, '0')}-01`
        const lastDay = new Date(year, month, 0).getDate()
        const endDate = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

        const { data: rides, error } = await supabase
          .from('rides')
          .select('id, date, time, activity_id, activities(name, color_hex, color, code), orders(pax, actual_pax)')
          .gte('date', startDate)
          .lte('date', endDate)
          .order('time')
        if (error) throw error

        // Raggruppa per data
        const byDate = {}
        for (const ride of (rides || [])) {
          if (!byDate[ride.date]) byDate[ride.date] = []
          const act = ride.activities || {}
          const orders = ride.orders || []
          const totalPax = orders.reduce((sum, o) => sum + (o.actual_pax || o.pax || 0), 0)
          byDate[ride.date].push({
            activity_code: act.code || act.name?.substring(0, 2)?.toUpperCase() || '??',
            color_hex: act.color_hex || act.color || '#607d8b',
            time: ride.time?.substring(0, 5) || '??:??',
            pax: totalPax,
            title: act.name || '',
            isGhost: false
          })
        }

        // Ghost Skeleton: per giorni senza ride, aggiungi ossatura
        const ghostMonthSlots = [
          { time: '09:00', title: 'Rafting Family', activity_code: 'FA' },
          { time: '11:00', title: 'Rafting Classic', activity_code: 'CL' },
          { time: '14:00', title: 'Hydrospeed Base', activity_code: 'HB' },
        ]

        // Genera griglia completa del mese
        const days = []
        for (let d = 1; d <= lastDay; d++) {
          const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
          const realRides = byDate[dateStr] || []
          days.push({
            date: dateStr,
            booked_rides: realRides.length > 0 ? realRides : ghostMonthSlots.map(g => ({
              activity_code: g.activity_code,
              color_hex: '#e0e0e0',
              time: g.time,
              pax: 0,
              title: g.title,
              isGhost: true,
            })),
            staff_count: 0,
          })
        }
        return days
      } catch (e) {
        console.error('[Supabase Error] fetchMonthOverviewSupabase:', e)
        const lastDay = new Date(year, month, 0).getDate()
        const days = []
        for (let d = 1; d <= lastDay; d++) {
          const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
          days.push({ date: dateStr, booked_rides: [], staff_count: 0 })
        }
        return days
      }
    },

    // --- SALVATAGGIO ORDINE SU SUPABASE ---
    async saveOrderToSupabase({ activityId, dateStr, timeStr, customerName, customerEmail, customerPhone, pax, totalPrice, status, notes }) {
      // Scudo UUID: traduce nome testuale in UUID se necessario
      let safeActId = activityId
      if (safeActId && !String(safeActId).includes('-')) {
        const matchedAct = this.activities.find(a => a.name.toLowerCase() === String(safeActId).toLowerCase())
        safeActId = matchedAct ? matchedAct.id : (this.activities.length > 0 ? this.activities[0].id : null)
        console.warn('[UUID Shield] Tradotto activityId da', activityId, 'a', safeActId)
      }

      // 1. Cerca se esiste già un ride per activity+date+time
      const { data: existingRides } = await supabase
        .from('rides')
        .select('id')
        .eq('activity_id', safeActId)
        .eq('date', dateStr)
        .eq('time', timeStr)
        .limit(1)

      let rideId
      if (existingRides && existingRides.length > 0) {
        rideId = existingRides[0].id
      } else {
        // 2. Crea nuovo ride
        const { data: newRide, error: rideErr } = await supabase
          .from('rides')
          .insert({ activity_id: safeActId, date: dateStr, time: timeStr, status: status || 'Disponibile' })
          .select()
          .single()
        if (rideErr) throw rideErr
        rideId = newRide.id
      }

      // 3. Crea l'ordine
      const { data: newOrder, error: orderErr } = await supabase
        .from('orders')
        .insert({
          ride_id: rideId,
          customer_name: customerName || 'Nuovo Cliente',
          customer_email: customerEmail || '',
          customer_phone: customerPhone || '',
          pax: parseInt(pax) || 1,
          total_price: parseFloat(totalPrice) || 0,
          status: status || 'CONFERMATO',
          notes: notes || ''
        })
        .select()
        .single()
      if (orderErr) throw orderErr

      // 4. Pre-genera slot vuoti in participants per il check-in Kiosk
      try {
        const paxCount = parseInt(pax) || 1
        const emptySlotsArray = Array.from({ length: paxCount }).map((_, index) => ({
          order_id: newOrder.id,
          name: index === 0 ? (customerName || 'Referente') : `Slot Vuoto #${index + 1}`,
          firaft_status: 'NON_RICHIESTO',
          is_privacy_signed: false,
          status: 'EMPTY',
          is_lead: index === 0
        }))
        await supabase.from('participants').insert(emptySlotsArray)
        console.log(`[Participants] Pre-generati ${paxCount} slot per ordine ${newOrder.id}`)
      } catch (partErr) {
        console.error('[Participants] Errore pre-generazione slot:', partErr)
        // Non blocca: l'ordine è già salvato
      }

      return rideId
    },

    selectResource(id) { this.selectedResourceId = id },

    // --- SALVATAGGIO ALLOCAZIONI RISORSE (con materializzazione ghost) ---
    async saveRideAllocationsSupabase(ride, resourceIds) {
      let actualRideId = ride.id || ride

      // Scudo UUID per activity_id
      let safeActId = ride.activity_id
      if (safeActId && !String(safeActId).includes('-')) {
        const matchedAct = this.activities.find(a => a.name.toLowerCase() === String(safeActId).toLowerCase())
        safeActId = matchedAct ? matchedAct.id : (this.activities.length > 0 ? this.activities[0].id : null)
        console.warn('[UUID Shield] Tradotto ride.activity_id da', ride.activity_id, 'a', safeActId)
      }

      // Materializza ghost nel DB se necessario
      if (String(actualRideId).startsWith('ghost-')) {
        const { data, error } = await supabase
          .from('rides')
          .insert({ activity_id: safeActId, date: ride.date, time: ride.time, status: 'Disponibile' })
          .select()
          .single()
        if (error) throw error
        actualRideId = data.id
      }

      // 1. Svuota le allocazioni esistenti per questo ride
      const { error: delErr } = await supabase
        .from('ride_allocations')
        .delete()
        .eq('ride_id', actualRideId)
      if (delErr) throw delErr

      // 2. Inserisci le nuove allocazioni
      if (resourceIds && resourceIds.length > 0) {
        const rows = resourceIds.map(rId => ({ ride_id: actualRideId, resource_id: rId }))
        const { error: insErr } = await supabase
          .from('ride_allocations')
          .insert(rows)
        if (insErr) throw insErr
      }

      return actualRideId
    },

    // --- PARTECIPANTI (FIRAFT) ---
    async fetchParticipantsForOrder(orderId) {
      try {
        const { data, error } = await supabase
          .from('participants')
          .select('*')
          .eq('order_id', orderId)
        if (error) {
          console.error('[Supabase Error] fetchParticipantsForOrder:', error)
          return []
        }
        return data || []
      } catch (e) {
        console.error('[Supabase Error] fetchParticipantsForOrder:', e)
        return []
      }
    }
  }
})

function _engineStatusDesc(engineStatus) {
  if (engineStatus === 'ROSSO') return 'Pieno / Chiuso'
  if (engineStatus === 'GIALLO') return 'Quasi Pieno'
  return 'Disponibile'
}
