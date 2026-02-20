/**
 * FiraftService — API Blueprint §11: API Esterna Tesseramento FiRaft
 *
 * Usa una propria istanza Axios perché l'autenticazione è diversa
 * (Bearer token fisso, non JWT WordPress).
 */
import axios from 'axios'

const firaftApi = axios.create({
  baseURL: import.meta.env.VITE_FIRAFT_API_URL,
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${import.meta.env.VITE_FIRAFT_TOKEN}`,
  },
})

export const FiraftService = {
  /**
   * POST /extApi/emitCard — Emissione tessera FiRaft
   * @param {Object} participantData — Dati del partecipante (vedi Blueprint §11.1)
   */
  emitCard(participantData) {
    return firaftApi.post('/emitCard', participantData)
  },
}
