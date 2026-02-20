<template>
  <div class="signature-wrapper">
    <div class="sig-canvas-container" ref="containerRef">
      <canvas ref="canvasRef" class="sig-canvas"></canvas>
    </div>
    <div class="row items-center justify-between q-pa-xs">
      <div class="text-caption text-grey-6 q-pl-xs">
        ✍️ {{ isEmpty ? hintText : '' }}
      </div>
      <q-btn
        icon="clear"
        size="sm"
        flat
        color="negative"
        :label="clearLabel"
        @click="clear"
        :disable="isEmpty"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import SignaturePadLib from 'signature_pad'
import { useRegistrationStore } from 'stores/registration-store'
import { translations } from 'src/constants/translations'

const props = defineProps({
  modelValue: { type: String, default: null },
  hintText: { type: String, default: 'Firma qui / Sign here' },
  penColor: { type: String, default: '#1a1a2e' },
  minWidth: { type: Number, default: 0.8 },
  maxWidth: { type: Number, default: 2.8 }
})

const emit = defineEmits(['update:modelValue', 'update:biometrics'])

let biometricPoints = []
let strokeStartTime = 0
const store = useRegistrationStore()
const t = computed(() => translations[store.language] || translations.it)
const clearLabel = computed(() => t.value.review?.clear || 'Pulisci')

// ── Refs ──
const canvasRef = ref(null)
const containerRef = ref(null)
const isEmpty = ref(true)

// ── Instance ──
let sigPad = null
let resizeObserver = null

/**
 * CRITICO: Ridimensionamento Canvas HiDPI-aware.
 * Il problema classico: il canvas CSS è "100% width" ma il backing store
 * è in pixel logici → su retina il tratto appare sgranato.
 * Soluzione: scaliamo il backing store per devicePixelRatio.
 */
function resizeCanvas () {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) return

  // Salviamo la firma corrente prima di ridimensionare (il resize cancella il canvas)
  const currentData = sigPad && !sigPad.isEmpty() ? sigPad.toData() : null

  const ratio = Math.max(window.devicePixelRatio || 1, 1)
  const width = container.clientWidth
  const height = 160 // Altezza fissa per consistenza UX

  // Imposta dimensioni CSS
  canvas.style.width = width + 'px'
  canvas.style.height = height + 'px'

  // Imposta dimensioni backing store (pixel fisici)
  canvas.width = Math.floor(width * ratio)
  canvas.height = Math.floor(height * ratio)

  // Scala il contesto 2D per matchare il devicePixelRatio
  const ctx = canvas.getContext('2d')
  ctx.scale(ratio, ratio)

  // Ripristina la firma se presente (dopo il resize il canvas si svuota)
  if (sigPad) {
    sigPad.clear() // Reset interno di signature_pad
    if (currentData) {
      sigPad.fromData(currentData)
    }
  }
}

/**
 * Inizializzazione del SignaturePad con la libreria signature_pad.
 * Cattura anche eventi per i dati biometrici.
 */
onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return

  // 1. Prima resize per impostare le dimensioni corrette
  resizeCanvas()

  // 2. Inizializza SignaturePad dalla libreria
  sigPad = new SignaturePadLib(canvas, {
    penColor: props.penColor,
    minWidth: props.minWidth,
    maxWidth: props.maxWidth,
    backgroundColor: 'rgba(255, 255, 255, 0)' // Trasparente per il PNG
  })

  // 3. Event handlers per biometria e stato
  sigPad.addEventListener('beginStroke', (event) => {
    biometricPoints = [] // Reset ad ogni nuovo tratto
    strokeStartTime = Date.now()

    // Cattura punto iniziale
    const point = event.detail
    if (point) {
      biometricPoints.push({
        x: Math.round(point.x),
        y: Math.round(point.y),
        t: 0,
        pressure: point.pressure || 0.5,
        type: 0 // begin
      })
    }
  })

  sigPad.addEventListener('endStroke', () => {
    // Punto finale
    biometricPoints.push({
      t: Date.now() - strokeStartTime,
      type: 2 // end
    })

    // Aggiorna stato vuoto
    isEmpty.value = sigPad.isEmpty()

    // Emetti immagine base64
    if (!sigPad.isEmpty()) {
      const dataUrl = sigPad.toDataURL('image/png')
      console.log('[SignaturePad] endStroke → emitting update:modelValue, length:', dataUrl.length)
      emit('update:modelValue', dataUrl)
      emit('update:biometrics', JSON.stringify(biometricPoints))
    } else {
      console.log('[SignaturePad] endStroke → pad is empty, NOT emitting')
    }
  })

  // Cattura ogni punto di movimento per i dati biometrici (FEA)
  canvas.addEventListener('pointermove', (e) => {
    if (sigPad.isEmpty() && biometricPoints.length === 0) return
    if (biometricPoints.length === 0) return // Non stiamo disegnando

    const rect = canvas.getBoundingClientRect()
    biometricPoints.push({
      x: Math.round(e.clientX - rect.left),
      y: Math.round(e.clientY - rect.top),
      t: Date.now() - strokeStartTime,
      pressure: e.pressure || 0.5,
      type: 1 // move
    })
  })

  // 4. ResizeObserver per ridimensionamento reattivo
  resizeObserver = new ResizeObserver(() => {
    resizeCanvas()
  })
  resizeObserver.observe(containerRef.value)

  // 5. Listener globale per orientamento schermo (mobile)
  window.addEventListener('resize', resizeCanvas)
})

onBeforeUnmount(() => {
  // Pulizia
  if (resizeObserver) {
    resizeObserver.disconnect()
    resizeObserver = null
  }
  window.removeEventListener('resize', resizeCanvas)

  if (sigPad) {
    sigPad.off()
    sigPad = null
  }
})

// ── Metodi esposti ──

function clear () {
  if (!sigPad) return
  sigPad.clear()
  biometricPoints = []
  isEmpty.value = true
  emit('update:modelValue', null)
  emit('update:biometrics', null)
}

function getImage () {
  if (!sigPad || sigPad.isEmpty()) return null
  return sigPad.toDataURL('image/png')
}

function checkIsEmpty () {
  return sigPad ? sigPad.isEmpty() : true
}

defineExpose({ clear, getImage, isEmpty: checkIsEmpty })
</script>

<style scoped>
.signature-wrapper {
  border: 2px dashed #b0bec5;
  background: #fafafa;
  border-radius: 12px;
  overflow: hidden;
  transition: border-color 0.3s ease;
}

.signature-wrapper:hover {
  border-color: #1976d2;
}

.sig-canvas-container {
  width: 100%;
  position: relative;
}

.sig-canvas {
  width: 100%;
  height: 160px;
  touch-action: none; /* Fondamentale: disabilita scroll/zoom durante la firma su mobile */
  cursor: crosshair;
  display: block; /* Evita gap sotto il canvas */
}
</style>
