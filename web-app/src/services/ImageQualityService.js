/**
 * ImageQualityService.js
 *
 * Implementazione leggera di algoritmi di Computer Vision lato client.
 * L'obiettivo è filtrare immagini di bassa qualità (sfocate, buie, mosse)
 * direttamente nel browser prima dell'invio al backend.
 *
 * Riferimento Strategia: Sezione 3 (Algoritmi di Validazione) [cite: 65]
 */

export default {
  /**
   * Converte i dati RGBA del Canvas in Scala di Grigi (Luminanza).
   * Formula: L = 0.299R + 0.587G + 0.114B [cite: 77]
   * @param {Uint8ClampedArray} data - Dati pixel (R, G, B, A, R, G, B, A...)
   * @returns {Uint8Array} Array di sola luminanza
   */
  convertToGrayscale (data) {
    const gray = new Uint8Array(data.length / 4)
    for (let i = 0; i < data.length; i += 4) {
      // i = Red, i+1 = Green, i+2 = Blue
      gray[i / 4] = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2]
    }
    return gray
  },

  /**
   * Calcola la luminosità media dell'immagine.
   * Utile per rilevare immagini sottoesposte o sovraesposte.
   * @param {Uint8Array} grayData - Array scala di grigi
   * @returns {number} Valore medio 0-255
   */
  calculateBrightness (grayData) {
    let sum = 0
    for (let i = 0; i < grayData.length; i++) {
      sum += grayData[i]
    }
    return Math.floor(sum / grayData.length)
  },

  /**
   * Rileva la nitidezza utilizzando una simulazione del filtro Laplaciano.
   * Calcola la varianza delle differenze tra pixel adiacenti (rilevamento bordi).
   * Una varianza alta indica bordi netti (a fuoco). Una bassa indica sfocatura.
   * Riferimento: Sezione 3.1 [cite: 70, 83]
   *
   * @param {Uint8Array} grayData - Array scala di grigi
   * @param {number} width - Larghezza immagine
   * @param {number} height - Altezza immagine
   * @returns {number} Punteggio di nitidezza (Varianza)
   */
  calculateBlurScore (grayData, width, height) {
    let sum = 0
    let sumSq = 0
    let count = 0

    // Kernel Laplaciano semplificato (croce):
    //  0  1  0
    //  1 -4  1
    //  0  1  0
    // Iteriamo saltando i bordi per evitare out-of-bounds
    for (let y = 1; y < height - 1; y++) {
      for (let x = 1; x < width - 1; x++) {
        const i = y * width + x

        // Convoluzione manuale per performance [cite: 78]
        const val =
          grayData[i - width] + // Top
          grayData[i - 1] +     // Left
          grayData[i + 1] +     // Right
          grayData[i + width] - // Bottom
          4 * grayData[i]       // Center

        sum += val
        sumSq += val * val
        count++
      }
    }

    const mean = sum / count
    const variance = (sumSq / count) - (mean * mean)
    return Math.floor(variance)
  },

  /**
   * Calcola la differenza quadratica media (MSE) tra due frame consecutivi.
   * Usato per rilevare se l'utente sta muovendo il telefono (Motion Detection).
   * Riferimento: Sezione 3.3 [cite: 97]
   *
   * @param {Uint8Array} currentGray - Frame corrente
   * @param {Uint8Array} previousGray - Frame precedente
   * @returns {number} Punteggio MSE (più è basso, più è stabile)
   */
  calculateStabilityMSE (currentGray, previousGray) {
    if (!previousGray || currentGray.length !== previousGray.length) return 9999

    // Ottimizzazione: campioniamo 1 pixel ogni 4 per velocità (downsampling implicito)
    // Non serve analizzare ogni pixel per rilevare il movimento macroscopico
    let errorSum = 0
    let count = 0
    const step = 4

    for (let i = 0; i < currentGray.length; i += step) {
      const diff = currentGray[i] - previousGray[i]
      errorSum += diff * diff
      count++
    }

    return errorSum / count
  },

  /**
   * Metodo helper che esegue l'analisi completa su dati ImageData.
   */
  analyzeFrame (imageData, previousGray = null) {
    const gray = this.convertToGrayscale(imageData.data)
    const brightness = this.calculateBrightness(gray)
    const blurScore = this.calculateBlurScore(gray, imageData.width, imageData.height)
    const stability = this.calculateStabilityMSE(gray, previousGray)

    return {
      grayBuffer: gray, // Da salvare per il prossimo ciclo come "previousGray"
      metrics: {
        brightness,
        blurScore,
        stability
      }
    }
  }
}