<template>
  <div class="camera-wrapper">
    <video 
      ref="video" 
      autoplay 
      playsinline 
      class="video-feed" 
      :class="{'mirrored': !isBackCamera, 'flash-effect': isFlashing}"
    ></video>
    
    <canvas ref="analysisCanvas" style="display: none;"></canvas>

    <div class="overlay-guide" :class="[docType, stateClass]">
      <div class="guide-border">
        <div class="guide-feedback transition-generic" v-if="feedbackMessage">
          <q-icon :name="feedbackIcon" size="sm" class="q-mr-xs" />
          {{ feedbackMessage }}
        </div>
      </div>
    </div>

    <div class="controls row justify-center items-center q-gutter-md">
      <q-btn round color="negative" icon="close" @click="stopCameraAndClose" />
      
      <q-btn round color="white" text-color="dark" icon="cameraswitch" @click="switchCamera" />
      
      <div class="relative-position">
        <q-circular-progress
          v-show="cameraState === 'ACQUIRING'"
          :value="acquireProgress"
          size="74px"
          thickness="0.15"
          color="green-5"
          track-color="transparent"
          class="absolute-center"
          show-value
        />
        
        <q-btn 
          round 
          :color="cameraState === 'ACQUIRING' ? 'yellow-9' : 'primary'" 
          icon="camera" 
          size="lg" 
          @click="forceCapture" 
        >
          <q-tooltip>Scatto Manuale</q-tooltip>
        </q-btn>
      </div>
    </div>

    <div v-if="showDebug" class="debug-overlay">
      <div>Blur: {{ debugMetrics.blur }} (Min: {{ THRESHOLDS.BLUR }})</div>
      <div>Bright: {{ debugMetrics.brightness }}</div>
      <div>Stable: {{ debugMetrics.stability }}</div>
      <div>State: {{ cameraState }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import ImageQualityService from 'src/services/ImageQualityService'

const props = defineProps({
  docType: { type: String, default: 'CIE' }
})
const emit = defineEmits(['capture', 'close'])

// --- Configurazione Soglie (Tuning Empirico) ---
// Riferimento Strategia Sez 3.1, 3.2, 3.3
const THRESHOLDS = {
  BLUR: 250,          // Sotto questo valore è sfocata (Varianza Laplaciano)
  BRIGHT_MIN: 60,     // Troppo scura
  BRIGHT_MAX: 230,    // Troppo chiara/sovraesposta
  STABILITY: 15,      // Differenza pixel tra frame (basso = stabile)
  DWELL_TIME: 1200    // Millisecondi di stabilità per scattare
}

// --- Stati ---
const video = ref(null)
const analysisCanvas = ref(null)
const stream = ref(null)
const isBackCamera = ref(true)
const isFlashing = ref(false)
const showDebug = ref(false) // Mettere true per debuggare i valori

// FSM: 'SEARCHING' | 'ACQUIRING' | 'LOCKED' | 'ERROR'
const cameraState = ref('SEARCHING') 
const acquireProgress = ref(0)
const feedbackMessage = ref('Inquadra il documento')
const feedbackIcon = ref('center_focus_strong')

// Variabili Loop Analisi
let analysisInterval = null
let lastFrameGray = null
let acquiringStartTime = 0

// Metriche reattive per debug
const debugMetrics = ref({ blur: 0, brightness: 0, stability: 0 })

// --- Computed UI ---
const stateClass = computed(() => {
  if (cameraState.value === 'ACQUIRING') return 'state-acquiring'
  if (cameraState.value === 'LOCKED') return 'state-locked'
  return 'state-searching'
})

// --- Gestione Fotocamera ---

async function startCamera() {
  stopCamera()
  
  // Richiesta FullHD per OCR ottimale
  const constraints = {
    video: {
      facingMode: isBackCamera.value ? 'environment' : 'user',
      width: { ideal: 1920 },
      height: { ideal: 1080 },
      focusMode: 'continuous' // Tentativo di forzare autofocus
    }
  }
  
  try {
    stream.value = await navigator.mediaDevices.getUserMedia(constraints)
    if (video.value) {
      video.value.srcObject = stream.value
      // Attendiamo che il video sia pronto prima di partire con l'analisi
      video.value.onloadedmetadata = () => {
        video.value.play()
        startAnalysisLoop()
      }
    }
  } catch (err) {
    console.error("Errore Camera:", err)
    feedbackMessage.value = "Errore accesso fotocamera"
    cameraState.value = 'ERROR'
  }
}

function stopCamera() {
  stopAnalysisLoop()
  if (stream.value) {
    stream.value.getTracks().forEach(track => track.stop())
    stream.value = null
  }
}

function stopCameraAndClose() {
  stopCamera()
  emit('close')
}

function switchCamera() {
  isBackCamera.value = !isBackCamera.value
  startCamera()
}

// --- Core Intelligence: Il Loop di Analisi ---

function startAnalysisLoop() {
  if (analysisInterval) clearInterval(analysisInterval)
  
  // Eseguiamo l'analisi ogni 150ms (~6-7 FPS) per non uccidere la CPU
  analysisInterval = setInterval(() => {
    if (!video.value || !analysisCanvas.value || cameraState.value === 'LOCKED') return
    
    processFrame()
  }, 150)
}

function stopAnalysisLoop() {
  if (analysisInterval) clearInterval(analysisInterval)
  analysisInterval = null
}

function processFrame() {
  const vid = video.value
  const can = analysisCanvas.value
  
  // Sincronizza dimensioni (fondamentale per i calcoli)
  // Usiamo una risoluzione ridotta per l'analisi per velocità (downsampling)
  const analysisWidth = 480 
  const scale = analysisWidth / vid.videoWidth
  const analysisHeight = vid.videoHeight * scale
  
  can.width = analysisWidth
  can.height = analysisHeight
  
  const ctx = can.getContext('2d', { willReadFrequently: true })
  ctx.drawImage(vid, 0, 0, can.width, can.height)
  
  try {
    const imageData = ctx.getImageData(0, 0, can.width, can.height)
    
    // Invocazione Service "Pure JS"
    const result = ImageQualityService.analyzeFrame(imageData, lastFrameGray)
    
    // Aggiorna buffer per il prossimo frame (Motion Detection)
    lastFrameGray = result.grayBuffer
    
    // Aggiorna metriche per logica
    const m = result.metrics
    debugMetrics.value = m // Per UI debug
    
    evaluateQuality(m)
    
  } catch (e) {
    console.warn("Frame analysis error:", e)
  }
}

// --- Macchina a Stati Decisionale (Logic Gatekeeper) ---

function evaluateQuality(metrics) {
  const isStable = metrics.stability < THRESHOLDS.STABILITY
  const isSharp = metrics.blurScore > THRESHOLDS.BLUR
  const isBrightEnough = metrics.brightness > THRESHOLDS.BRIGHT_MIN
  const isNotTooBright = metrics.brightness < THRESHOLDS.BRIGHT_MAX
  
  // 1. Check Errori Bloccanti
  if (!isBrightEnough) {
    resetAcquisition('Troppo buio 🌑', 'brightness_low')
    return
  }
  if (!isNotTooBright) {
    resetAcquisition('Troppo chiaro / Riflessi ☀️', 'brightness_high')
    return
  }
  
  // 2. Check Movimento
  if (!isStable) {
    resetAcquisition('Tieni fermo il telefono ✋', 'vibration')
    return
  }
  
  // 3. Check Fuoco (Solo se stabile)
  if (!isSharp) {
    resetAcquisition('Metti a fuoco (Tocca schermo) 🎯', 'blur_on')
    return
  }
  
  // 4. Tutto OK -> Transizione ACQUIRING -> LOCKED
  if (cameraState.value !== 'ACQUIRING') {
    // Entra in stato acquisizione
    cameraState.value = 'ACQUIRING'
    acquiringStartTime = Date.now()
    feedbackMessage.value = 'Non muoverti...'
    feedbackIcon.value = 'timer'
  } else {
    // Siamo già in acquisizione, aggiorna progresso
    const elapsed = Date.now() - acquiringStartTime
    const progress = Math.min(100, (elapsed / THRESHOLDS.DWELL_TIME) * 100)
    acquireProgress.value = progress
    
    if (elapsed >= THRESHOLDS.DWELL_TIME) {
      // Successo! Scatto automatico
      captureImage(true)
    }
  }
}

function resetAcquisition(msg, icon) {
  if (cameraState.value === 'ACQUIRING') {
    // Interruzione durante il caricamento
    acquireProgress.value = 0
  }
  cameraState.value = 'SEARCHING'
  feedbackMessage.value = msg
  feedbackIcon.value = icon
}

// --- Cattura ---

function forceCapture() {
  // Scatto manuale (Escape Hatch)
  captureImage(false)
}

function captureImage(isAuto) {
  if (cameraState.value === 'LOCKED') return // Già preso
  
  stopAnalysisLoop()
  cameraState.value = 'LOCKED'
  feedbackMessage.value = isAuto ? 'Preso! ✅' : 'Scatto Manuale 📸'
  acquireProgress.value = 100
  
  // Effetto Flash Visivo
  isFlashing.value = true
  setTimeout(() => isFlashing.value = false, 300)
  
  // Cattura alla MASSIMA risoluzione (dal video source, non dal canvas di analisi)
  const vid = video.value
  const fullCanvas = document.createElement('canvas')
  fullCanvas.width = vid.videoWidth
  fullCanvas.height = vid.videoHeight
  
  const ctx = fullCanvas.getContext('2d')
  
  // Gestione mirroring fronte/retro
  if (!isBackCamera.value) {
    ctx.translate(fullCanvas.width, 0)
    ctx.scale(-1, 1)
  }
  
  ctx.drawImage(vid, 0, 0, fullCanvas.width, fullCanvas.height)
  
  fullCanvas.toBlob((blob) => {
    // Crea file e invia al genitore
    const file = new File([blob], `scan_${props.docType}_${Date.now()}.jpg`, { type: "image/jpeg" })
    
    // Piccolo delay per far vedere l'animazione di successo
    setTimeout(() => {
      emit('capture', file)
      stopCamera() // Importante: rilascia risorse
    }, 500)
    
  }, 'image/jpeg', 0.95) // Max qualità per backend OCR
}

onMounted(() => {
  startCamera()
})

onUnmounted(() => {
  stopCamera()
})
</script>

<style scoped>
.camera-wrapper {
  position: relative;
  width: 100%;
  height: 60vh; /* Responsive height */
  min-height: 400px;
  background: #000;
  overflow: hidden;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
}

.video-feed {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.1s;
}

.mirrored {
  transform: scaleX(-1);
}

.flash-effect {
  opacity: 0.2;
  filter: brightness(10);
}

/* OVERLAY GUIDE & STATES */
.overlay-guide {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none; /* Lascia passare i click */
  transition: all 0.3s ease;
}

.guide-border {
  border: 3px solid rgba(255, 255, 255, 0.6); /* Default Searching */
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.6); /* Darken outside */
  border-radius: 16px;
  position: relative;
  transition: border-color 0.3s ease, transform 0.2s ease;
}

/* State Colors */
.state-searching .guide-border { border-color: rgba(255, 255, 255, 0.8); }
.state-acquiring .guide-border { border-color: #fdd835; /* Yellow */ transform: scale(1.02); }
.state-locked .guide-border { border-color: #21ba45; /* Green */ box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.8); }

/* Feedback Text pill */
.guide-feedback {
  position: absolute;
  bottom: -50px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 6px 12px;
  border-radius: 20px;
  white-space: nowrap;
  font-weight: 500;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
}

/* Aspect Ratios per Doc Type */
.CIE .guide-border, .PATENTE_IT .guide-border, .CI_CARTACEA .guide-border, .PERMESSO_SOGGIORNO .guide-border {
  width: 85%;
  aspect-ratio: 85.6 / 53.98; 
  max-width: 500px;
}
.PASSAPORTO .guide-border {
  width: 80%;
  aspect-ratio: 125 / 88; /* Passaporto aperto */
  max-width: 500px;
}

.controls {
  position: absolute;
  bottom: 30px;
  width: 100%;
  z-index: 10;
  pointer-events: auto;
}

.debug-overlay {
  position: absolute;
  top: 10px;
  left: 10px;
  background: rgba(0,0,0,0.5);
  color: lime;
  font-family: monospace;
  font-size: 10px;
  padding: 4px;
  pointer-events: none;
}

/* Transition Utility */
.transition-generic { transition: all 0.3s ease; }
</style>