<template>
  <div class="signature-wrapper">
    <canvas ref="canvasRef" class="sig-canvas"></canvas>
    <div class="row justify-end q-pa-xs">
      <q-btn icon="refresh" size="sm" flat label="Pulisci" @click="clear" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, defineExpose, defineEmits } from 'vue'

// Definiamo un nuovo evento 'update:biometrics' per passare i dati grezzi
const emit = defineEmits(['update:modelValue', 'update:biometrics'])
const canvasRef = ref(null)
let ctx = null
let drawing = false

// Variabili per Grafometria (Compliance Legale FEA)
let points = []
let startTime = 0

onMounted(() => {
  const c = canvasRef.value
  if(!c) return
  
  // Setup Canvas
  c.width = c.parentElement.clientWidth
  c.height = 150
  ctx = c.getContext('2d')
  ctx.lineWidth = 2
  ctx.strokeStyle = '#000'
  
  const getPos = (e) => {
    const r = c.getBoundingClientRect();
    const clientX = e.touches ? e.touches[0].clientX : e.clientX;
    const clientY = e.touches ? e.touches[0].clientY : e.clientY;
    return { x: clientX - r.left, y: clientY - r.top }
  }

  const start = (e) => { 
    drawing = true;
    points = []; // Reset dati biometrici all'inizio di una nuova firma
    startTime = Date.now();
    
    ctx.beginPath(); 
    const {x,y} = getPos(e); 
    ctx.moveTo(x,y); 
    
    // Salva punto iniziale (type 0)
    points.push({ x: Math.round(x), y: Math.round(y), t: 0, type: 0 });
  }
  
  const move = (e) => { 
    if(!drawing) return;
    const {x,y} = getPos(e); 
    
    ctx.lineTo(x,y); 
    ctx.stroke(); 
    
    // Salva punto movimento con delta temporale (type 1)
    // Questo permette di calcolare velocità e accelerazione (Ductus)
    points.push({ x: Math.round(x), y: Math.round(y), t: Date.now() - startTime, type: 1 });
  }
  
  const end = () => { 
    drawing = false;
    // Salva punto fine (type 2)
    points.push({ t: Date.now() - startTime, type: 2 });
    
    // 1. Emette l'immagine base (per visualizzazione nel PDF)
    emit('update:modelValue', getImage()) 
    
    // 2. Emette i dati biometrici (per hashing e validità legale)
    // Questo JSON verrà usato per creare l'hash univoco della firma
    emit('update:biometrics', JSON.stringify(points))
  }
  
  c.addEventListener('mousedown', start);
  c.addEventListener('mousemove', move); 
  c.addEventListener('mouseup', end);
  // Touch events (passive: false per prevenire lo scroll)
  c.addEventListener('touchstart', start, {passive: false});
  c.addEventListener('touchmove', move, {passive: false}); 
  c.addEventListener('touchend', end);
})

const clear = () => {
  if (!ctx || !canvasRef.value) return
  ctx.clearRect(0,0, canvasRef.value.width, canvasRef.value.height)
  points = []
  emit('update:modelValue', null)
  emit('update:biometrics', null)
}

const getImage = () => canvasRef.value.toDataURL('image/png')
const isEmpty = () => points.length === 0

defineExpose({ clear, getImage, isEmpty })
</script>

<style scoped>
.signature-wrapper {
  border: 1px dashed #ccc;
  background: white;
  border-radius: 4px;
}
.sig-canvas {
  width: 100%; 
  height: 150px; 
  touch-action: none; /* Fondamentale per mobile */
  cursor: crosshair;
}
</style>