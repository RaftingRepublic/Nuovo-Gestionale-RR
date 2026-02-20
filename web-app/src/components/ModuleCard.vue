<template>
  <q-card class="cursor-pointer q-hoverable transition-generic" v-ripple @click="$emit('click')">
    <q-card-section class="flex flex-center column q-py-lg">
      <div
        class="flex flex-center q-mb-md"
        :style="`background-color: ${hexToRgba(color, 0.1)}; width: 60px; height: 60px; border-radius: 50%;`"
      >
        <q-icon :name="icon" size="30px" :style="`color: ${color}`" />
      </div>

      <div class="text-subtitle1 text-weight-bold">{{ title }}</div>
      <div v-if="caption" class="text-caption text-grey-7 q-mt-xs text-center">
        {{ caption }}
      </div>
    </q-card-section>
  </q-card>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  icon: { type: String, required: true },
  color: { type: String, default: '#1976D2' },
  caption: { type: String, default: '' }
})

defineEmits(['click'])

function hexToRgba (hex, alpha) {
  if (!hex || typeof hex !== 'string' || !hex.startsWith('#') || hex.length !== 7) {
    return `rgba(0, 0, 0, ${alpha})`
  }
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}
</script>

<style scoped>
.transition-generic { transition: transform 0.2s; }
.transition-generic:hover { transform: translateY(-5px); }
</style>
