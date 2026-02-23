<template>
  <q-dialog v-model="isOpen">
    <q-card style="min-width: 300px" class="text-center q-pa-md">
      <q-card-section>
        <div class="text-h6">Inquadra per Registrarti</div>
        <div class="text-caption text-grey">Fai inquadrare questo codice al cliente</div>
      </q-card-section>
      <q-card-section class="q-pt-none flex flex-center">
        <q-img :src="url" style="width: 250px; height: 250px" fit="contain" spinner-color="primary" />
      </q-card-section>
      <q-card-actions align="right">
        <q-btn flat label="Chiudi" color="primary" v-close-popup />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ modelValue: Boolean, url: String })
const emit = defineEmits(['update:modelValue'])
const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})
</script>
