import { defineStore } from 'pinia'
import { api } from 'boot/axios'

export const useReservationStore = defineStore('reservation', {
    state: () => ({
        reservations: [],
        loading: false
    }),

    getters: {
        getBySlot: (state) => (date, time, type) => {
            // Date format in store might be YYYY-MM-DD. 
            return state.reservations.filter(r => r.date === date && r.time === time && r.activity_type === type)
        }
    },

    actions: {
        async fetchReservations(date) {
            if (!date) return
            this.loading = true
            try {
                const res = await api.get('/reservations/', { params: { date } })
                this.reservations = res.data
            } catch (e) {
                console.error('Error fetching reservations:', e)
                throw e
            } finally {
                this.loading = false
            }
        },

        async addReservation(payload) {
            this.loading = true
            try {
                const res = await api.post('/reservations/', payload)
                this.reservations.push(res.data)
                return res.data
            } catch (e) {
                console.error('Error adding reservation:', e)
                throw e
            } finally {
                this.loading = false
            }
        },

        async deleteReservation(id) {
            try {
                await api.delete(`/reservations/${id}`)
                this.reservations = this.reservations.filter(r => r.id !== id)
            } catch (e) {
                console.error('Error deleting reservation:', e)
                throw e
            }
        }
    }
})
