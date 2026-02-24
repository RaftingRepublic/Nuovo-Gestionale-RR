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
    activities: [],    // Catalogo attività da SQLite (Single Source of Truth: code, color_hex, activity_class)
    resources: [],     // Catalogo risorse Supabase (bridge UUID per ride_allocations)
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
    // ── Helper: Filtro Stagionale per Ghost Slots ──
    _isDateInSeason(targetDateStr, seasonStart, seasonEnd) {
      const target = new Date(targetDateStr)
      target.setHours(0, 0, 0, 0)

      if (seasonStart) {
        const start = new Date(seasonStart)
        start.setHours(0, 0, 0, 0)
        if (target < start) return false
      }
      if (seasonEnd) {
        const end = new Date(seasonEnd)
        end.setHours(23, 59, 59, 999)
        if (target > end) return false
      }
      return true
    },

    // ── Helper: Validazione eccezioni (Chiusure Totali) ──
    _isActivityClosedOnDate(act, dateStr) {
      const exceptions = act.sub_periods || []
      if (!Array.isArray(exceptions)) return false

      return exceptions.some(exc => {
        const isClosed = exc.is_closed === true
        if (!isClosed) return false

        // Verifica se la data target è inclusa nell'array dates
        if (Array.isArray(exc.dates) && exc.dates.includes(dateStr)) return true

        return false
      })
    },

    // ── Helper: Parsing sicuro degli orari attività ──
    _parseDefaultTimes(act) {
      let times = act.default_times || act.slots || []
      if (typeof times === 'string') {
        try { times = JSON.parse(times) } catch { times = [] }
      }
      if (!Array.isArray(times)) return []
      return times
        .filter(t => t && typeof t === 'string' && t.trim() !== '' && t !== '--:--')
        .map(t => t.trim().substring(0, 5))
    },

    // --- CATALOGHI (Single Source of Truth: SQLite via FastAPI) ---
    async fetchCatalogs() {
      try {
        // Attività: UNICA fonte è SQLite (ha code, color_hex, activity_class)
        const actRes = await api.get('/calendar/activities')
        this.activities = Array.isArray(actRes.data) ? actRes.data : (actRes.data?.activities || [])

        // Risorse Supabase: servono SOLO come bridge UUID per ride_allocations
        try {
          const { data: res, error: errRes } = await supabase.from('resources').select('*').order('name')
          if (!errRes && res) this.resources = res
        } catch (e) {
          console.warn('[Store] Supabase resources fetch fallito (non bloccante):', e)
        }
      } catch (err) {
        console.error('[Store] Errore fetch cataloghi:', err)
        throw err
      }
    },

    // --- STAFF ---
    async fetchStaff() {
      try {
        const rawData = (await api.get('/logistics/staff')).data
        this.staffList = rawData.map(s => {
          let safeRoles = []
          if (Array.isArray(s.roles)) {
            safeRoles = s.roles
          } else if (s.roles) {
            try {
              safeRoles = JSON.parse(s.roles)
              if (!Array.isArray(safeRoles)) safeRoles = []
            } catch {
              safeRoles = String(s.roles).split(',').map(str => str.replace(/[^a-zA-Z0-9_-]/g, '').trim().toUpperCase()).filter(str => str)
            }
          }
          return { ...s, roles: safeRoles }
        })
      } catch (e) { console.error(e) }
    },
    async addStaff(payload) {
      const res = await api.post('/logistics/staff', payload)
      this.staffList.push(res.data)
    },
    async deleteStaff(id) {
      // 1. Trova il nome per il cleanup Supabase
      const staff = this.staffList.find(s => s.id === id)
      const staffName = staff?.name || ''

      // 2. Soft-delete su SQLite
      await api.delete(`/logistics/staff/${id}`)

      // 3. Cleanup Split-Brain: rimuovi da Supabase resources per nome
      if (staffName) {
        try {
          await supabase.from('resources').delete().ilike('name', staffName.trim())
        } catch (e) {
          console.warn('[Store] Supabase cleanup staff fallito (non bloccante):', e)
        }
      }

      // 4. Aggiorna stato locale
      this.staffList = this.staffList.filter(s => s.id !== id)
      if (this.selectedResourceId === id) this.selectedResourceId = null

      // 5. Ricarica catalogo risorse Supabase per sincronizzare le tendine
      try { await this.fetchCatalogs() } catch { /* silenzioso */ }
    },
    async deleteFleet(id) {
      // 1. Trova il nome per il cleanup Supabase
      const fleet = this.fleetList.find(f => f.id === id)
      const fleetName = fleet?.name || ''

      // 2. Soft-delete su SQLite
      await api.delete(`/logistics/fleet/${id}`)

      // 3. Cleanup Split-Brain: rimuovi da Supabase resources per nome
      if (fleetName) {
        try {
          await supabase.from('resources').delete().ilike('name', fleetName.trim())
        } catch (e) {
          console.warn('[Store] Supabase cleanup fleet fallito (non bloccante):', e)
        }
      }

      // 4. Aggiorna stato locale
      this.fleetList = this.fleetList.filter(f => f.id !== id)
      if (this.selectedResourceId === id) this.selectedResourceId = null

      // 5. Ricarica catalogo risorse Supabase per sincronizzare le tendine
      try { await this.fetchCatalogs() } catch { /* silenzioso */ }
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
    async updateFleet(fleetId, payload) {
      const res = await api.patch(`/logistics/fleet/${fleetId}`, payload)
      const idx = this.fleetList.findIndex(f => f.id === fleetId)
      if (idx !== -1) this.fleetList[idx] = res.data
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
    async fetchDailySchedule(dateStr) {
      this.loading = true
      try {
        const { data, error } = await supabase
          .from('rides')
          .select('*, orders(*), ride_allocations(*, resources(*))')
          .eq('date', dateStr)
          .order('time')
        if (error) console.error('[Supabase] fetchDailySchedule error (non bloccante):', error)

        const mappedRides = (data || []).map(ride => {
          const orders = ride.orders || []
          const allocs = ride.ride_allocations || []
          const bookedPax = orders.reduce((sum, o) => sum + (o.actual_pax || o.pax || 0), 0)
          // Decorazione da SQLite (Single Source of Truth per code/color) — NO FK activities
          const act = (this.activities || []).find(a => String(a.id) === String(ride.activity_id)) || {}
          return {
            id: ride.id,
            time: ride.time,
            activity_type: act.name || ride.activity_type || 'Sconosciuta',
            activity_name: act.name || ride.activity_name || 'Sconosciuta',
            activity_id: ride.activity_id,
            activity_code: act.code || ride.activity_code || 'RA',
            activity_class: act.activity_class || 'RAFTING',
            color_hex: act.color_hex || act.color || ride.color_hex || '#607d8b',
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
            duration_hours: act.duration_hours || 2,
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
            drivers: allocs.filter(a => a && a.resources && a.resources.type === 'driver').map(a => a.resources),
            rafts: allocs.filter(a => a && a.resources && a.resources.type === 'raft').map(a => a.resources),
            vans: allocs.filter(a => a && a.resources && a.resources.type === 'van').map(a => a.resources),
            trailers: allocs.filter(a => a && a.resources && a.resources.type === 'trailer').map(a => a.resources),
            isGhost: false,
            date: dateStr,
          }
        })

        // Ghost Skeleton DINAMICO: genera slot vuoti dagli orari configurati nelle attività SQLite
        // NESSUN ORARIO HARDCODATO — tutto viene da this.activities (default_times + season_start/season_end)

        try {
          const storeActivities = Array.isArray(this.activities) ? this.activities : []
          const ghosts = []

          for (const act of storeActivities) {
            if (!act || !act.name) continue

            // Filtro stagionale: salta attività fuori stagione
            if (!this._isDateInSeason(dateStr, act.season_start, act.season_end)) continue

            // Filtro eccezioni: salta giorni di chiusura totale
            if (this._isActivityClosedOnDate(act, dateStr)) continue

            // Parsing orari configurati per questa attività
            const actTimes = this._parseDefaultTimes(act)
            if (actTimes.length === 0) continue

            for (const time of actTimes) {
              // Non generare ghost se esiste già un turno reale a quest'ora per questa attività
              const alreadyExists = mappedRides.some(r =>
                r && r.time && String(r.time).startsWith(time) &&
                (String(r.activity_id) === String(act.id) || String(r.activity_type || '').toLowerCase() === act.name.toLowerCase())
              )
              if (alreadyExists) continue

              // Non generare ghost se c'è già un ghost a quest'ora per un'altra attività
              const ghostExists = ghosts.some(g => g.time === time + ':00')
              if (ghostExists) continue

              const cap = act.default_capacity || 16

              ghosts.push({
                id: 'ghost-' + time.replace(':', '') + '-' + String(act.id).substring(0, 8),
                time: time + ':00',
                activity_type: act.name,
                activity_name: act.name,
                activity_id: act.id,
                activity_code: act.code || String(act.name).substring(0, 2).toUpperCase(),
                activity_class: act.activity_class || 'RAFTING',
                title: act.name,
                color: act.color_hex || '#90a4ae',
                color_hex: act.color_hex || '#90a4ae',
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
        console.error('[Supabase Error] fetchDailySchedule:', e)
        this.dailySchedule.splice(0, this.dailySchedule.length)
      }
      finally { this.loading = false }
    },

    async fetchMonthOverview(year, month) {
      try {
        // Precarica attività SQLite se non ancora disponibili
        if (!this.activities.length) await this.fetchCatalogs()

        const startDate = `${year}-${String(month).padStart(2, '0')}-01`
        const lastDay = new Date(year, month, 0).getDate()
        const endDate = `${year}-${String(month).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`

        const { data, error } = await supabase
          .from('rides')
          .select('id, date, time, activity_id, orders(pax, actual_pax), ride_allocations(resource_id,resources(name,type))')
          .gte('date', startDate)
          .lte('date', endDate)
          .order('time')
        if (error) {
          console.error('[Supabase] fetchMonthOverview error (non bloccante):', error)
        }

        // Merge reali + ghost DINAMICI (basati su this.activities)
        const sourceRides = Array.isArray(data) ? data : []

        const daysInMonth = new Date(year, month, 0).getDate()
        const yStr = String(year)
        const mStr = String(month).padStart(2, '0')
        const days = []
        const storeActs = Array.isArray(this.activities) ? this.activities : []

        for (let i = 1; i <= daysInMonth; i++) {
          const dStr = `${yStr}-${mStr}-${String(i).padStart(2, '0')}`
          const dayRides = sourceRides.filter(r => r.date && String(r.date).split('T')[0] === dStr)

          // 1. Mappa i turni REALI dal DB (MAI filtrati)
          let realMapped = []
          if (dayRides.length > 0) {
            realMapped = dayRides.map(r => {
              const paxCount = r.orders
                ? r.orders.reduce((sum, o) => sum + (o.actual_pax !== undefined && o.actual_pax !== null ? Number(o.actual_pax) : (Number(o.pax) || 0)), 0)
                : 0
              const sqlAct = storeActs.find(a => String(a.id) === String(r.activity_id)) || {}
              const actName = sqlAct.name || r.activity_name || 'Turno'
              const actCode = sqlAct.code || (actName ? String(actName).substring(0, 2).toUpperCase() : 'XX')
              const actColor = sqlAct.color_hex || sqlAct.color || '#2196f3'
              return {
                id: r.id,
                activity_id: r.activity_id,
                time: r.time ? String(r.time).substring(0, 5) : '',
                activity_code: actCode,
                title: actName,
                color_hex: actColor,
                pax: paxCount,
                isGhost: false,
                allocations: Array.isArray(r.ride_allocations)
                  ? r.ride_allocations
                      .filter(a => a && a.resources)
                      .map(a => ({ resource_name: a.resources.name, resource_type: a.resources.type }))
                  : []
              }
            })
          }

          // 2. Ghost DINAMICI da this.activities (nessun hardcode)
          const ghosts = []
          for (const act of storeActs) {
            if (!act || !act.name) continue

            // Filtro stagionale
            if (!this._isDateInSeason(dStr, act.season_start, act.season_end)) continue

            // Filtro eccezioni: chiusura totale
            if (this._isActivityClosedOnDate(act, dStr)) continue

            const actTimes = this._parseDefaultTimes(act)
            if (actTimes.length === 0) continue

            for (const time of actTimes) {
              // Non creare ghost se c'è già un ride reale a quest'ora per quest'attività
              const alreadyExists = realMapped.some(r =>
                r.time === time && (String(r.activity_id) === String(act.id))
              )
              if (alreadyExists) continue

              // Non duplicare ghost sullo stesso orario
              const ghostExists = ghosts.some(g => g.time === time)
              if (ghostExists) continue

              ghosts.push({
                id: 'ghost-m-' + dStr + '-' + time.replace(':', '') + '-' + String(act.id).substring(0, 8),
                time: time,
                activity_id: act.id,
                activity_code: act.code || String(act.name).substring(0, 2).toUpperCase(),
                title: act.name,
                color_hex: act.color_hex || '#90a4ae',
                pax: 0,
                isGhost: true
              })
            }
          }

          // 3. Fonde e ordina cronologicamente
          const combined = [...realMapped, ...ghosts].sort((a, b) => String(a.time || '').localeCompare(String(b.time || '')))

          days.push({
            date: dStr,
            booked_rides: combined,
            staff_count: 0
          })
        }

        return days
      } catch (e) {
        console.error('[Supabase Error] fetchMonthOverview:', e)
        // Fallback dinamico: usa this.activities se disponibili, altrimenti griglia vuota
        const fallbackActs = Array.isArray(this.activities) ? this.activities : []
        const lastDay = new Date(year, month, 0).getDate()
        const days = []
        for (let d = 1; d <= lastDay; d++) {
          const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`
          const ghosts = []
          for (const act of fallbackActs) {
            if (!act || !act.name) continue
            if (!this._isDateInSeason(dateStr, act.season_start, act.season_end)) continue
            if (this._isActivityClosedOnDate(act, dateStr)) continue
            const actTimes = this._parseDefaultTimes(act)
            for (const time of actTimes) {
              if (ghosts.some(g => g.time === time)) continue
              ghosts.push({
                id: 'ghost-m-' + dateStr + '-' + time.replace(':', '') + '-' + String(act.id).substring(0, 8),
                time: time,
                activity_id: act.id,
                activity_code: act.code || String(act.name).substring(0, 2).toUpperCase(),
                title: act.name,
                color_hex: act.color_hex || '#90a4ae',
                pax: 0,
                isGhost: true
              })
            }
          }
          days.push({
            date: dateStr,
            booked_rides: ghosts.sort((a, b) => (a.time || '').localeCompare(b.time || '')),
            staff_count: 0
          })
        }
        return days
      }
    },

    // --- SALVATAGGIO ORDINE SU SUPABASE ---
    async saveOrder({ activityId, dateStr, timeStr, customerName, customerEmail, customerPhone, pax, totalPrice, status, notes }) {
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
      } catch (partErr) {
        console.error('[Participants] Errore pre-generazione slot:', partErr)
        // Non blocca: l'ordine è già salvato
      }

      return rideId
    },

    selectResource(id) { this.selectedResourceId = id },

    // --- AUTO-HEALING: Name → UUID Supabase (Upsert JIT) ---
    async ensureSupabaseIds(payload) {
      if (!payload || payload.length === 0) return []

      // 1. Scarica tutte le risorse da Supabase per match robusto lato client
      const { data: allResources, error: fetchErr } = await supabase
        .from('resources').select('id, name, type')
      if (fetchErr) throw fetchErr

      // 2. Crea mappa lowercase per ricerca O(1)
      const existingLowerMap = {}
      ;(allResources || []).forEach(r => {
        if (r.name) existingLowerMap[r.name.trim().toLowerCase()] = r.id
      })

      const toInsert = []
      const nameToUuidMap = {}

      // 3. Analizza il payload
      payload.forEach(item => {
        if (!item.name) return
        const cleanName = item.name.trim().toLowerCase()

        if (existingLowerMap[cleanName]) {
          // Esiste già nello storico (es. "Stefano")
          nameToUuidMap[item.name] = existingLowerMap[cleanName]
        } else {
          // Da creare. Evitiamo duplicati multipli nello stesso payload
          if (!toInsert.some(i => i.name.trim().toLowerCase() === cleanName)) {
            toInsert.push({ name: item.name.trim(), type: item.type || 'guide' })
          }
        }
      })

      // 4. Inserisci i mancanti in blocco
      if (toInsert.length > 0) {
        const { data: inserted, error: insertErr } = await supabase
          .from('resources').insert(toInsert).select('id, name')
        if (insertErr) throw insertErr

        ;(inserted || []).forEach(r => {
          const original = payload.find(p =>
            p.name.trim().toLowerCase() === r.name.trim().toLowerCase()
          )
          if (original) nameToUuidMap[original.name] = r.id
        })
      }

      // 5. Aggiorna il catalogo locale per coerenza
      try { await this.fetchCatalogs() } catch { /* silenzioso */ }

      // 6. Mappa il payload originale agli UUID validi
      return payload.map(p => nameToUuidMap[p.name]).filter(id => id)
    },

    // --- SALVATAGGIO ALLOCAZIONI RISORSE (con materializzazione ghost) ---
    async saveRideAllocations(ride, resourceIds) {
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
