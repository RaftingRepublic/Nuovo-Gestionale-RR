<template>
  <div class="row q-col-gutter-lg">
    <div class="col-12" v-if="store.isEditMode">
      <q-banner class="bg-warning text-dark q-mb-md">
        <q-icon name="lock" /> <strong>{{ t.review.edit_warning }}</strong>
      </q-banner>
    </div>

    <div class="col-12" v-if="store.tutorParticipates || !store.hasMinors">
      <q-card bordered class="shadow-1">
        <q-card-section class="bg-primary text-white">
          <div class="text-h6">{{ store.hasMinors ? 'Tutore' : 'Partecipante' }}</div>
        </q-card-section>
        <q-card-section>
          <PersonForm 
            v-model="store.guardian.ocrData" 
            :is-adult="true"
            :readonly="store.isEditMode"
          />
        </q-card-section>
      </q-card>
    </div>

    <div v-if="store.hasMinors" class="col-12">
      <div v-for="(minor, idx) in store.minors" :key="minor.id" class="q-mb-md">
        <q-card bordered class="shadow-1">
          <q-card-section class="bg-secondary text-white">
            <div class="text-h6">Minore #{{ idx + 1 }}</div>
          </q-card-section>
          <q-card-section>
             <PersonForm 
              v-model="minor.ocrData" 
              :is-adult="false"
              :readonly="store.isEditMode"
            />
            <div class="q-mt-md">
              <div class="text-subtitle2 q-mb-sm">{{ t.review.minor_sig_title }} #{{ idx + 1 }}</div>
              <SignaturePad 
                v-model="minor.ocrData.signature" 
                @update:biometrics="(val) => minor.ocrData.signatureBiometrics = val"
              />
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>

    <div class="col-12" v-if="store.tutorParticipates || !store.hasMinors">
      <q-card bordered class="bg-grey-1">
        <q-card-section>
          <div class="text-subtitle1 text-weight-bold">{{ t.review.main_sig_title }}</div>
          <div class="text-caption text-grey-7 q-mb-sm">{{ t.review.main_sig_desc }}</div>
          <SignaturePad 
            v-model="store.guardian.ocrData.signature"
            @update:biometrics="(val) => store.guardian.ocrData.signatureBiometrics = val"
          />
        </q-card-section>
      </q-card>
    </div>

    <div class="col-12 row justify-between q-mt-lg">
      <q-btn flat :label="t.nav.back" v-on:click="$emit('prev')" />
      <q-btn color="primary" label="Vai al Riepilogo" v-on:click="$emit('next')" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRegistrationStore } from 'stores/registration-store'
import { translations } from 'src/constants/translations' 
import PersonForm from '../PersonForm.vue'
import SignaturePad from '../SignaturePad.vue'

defineEmits(['next', 'prev'])

const store = useRegistrationStore()
const t = computed(() => translations[store.language] || translations.it)
</script>