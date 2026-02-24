<template>
  <q-page class="q-pa-md" style="max-width: 900px; margin: 0 auto;">

    <!-- ─── HEADER ──────────────────────────────────── -->
    <div class="row items-center q-mb-lg">
      <q-icon name="tune" size="32px" color="primary" class="q-mr-sm" />
      <div>
        <div class="text-h5 text-weight-bold">Pannello Variabili</div>
        <div class="text-caption text-grey-7">
          Configura tempi logistici e capienze dei mezzi
        </div>
      </div>
      <q-space />
      <q-btn
        label="Salva Impostazioni"
        icon="save"
        color="primary"
        unelevated
        :loading="settingsStore.loading"
        :disable="settingsStore.loading"
        @click="saveSettings"
      />
    </div>

    <!-- ─── LOADING ─────────────────────────────────── -->
    <div v-if="settingsStore.loading && settingsStore.settings.length === 0" class="text-center q-pa-xl">
      <q-spinner-dots size="40px" color="primary" />
      <div class="q-mt-md text-grey-6">Caricamento impostazioni...</div>
    </div>

    <!-- ─── ERRORE ──────────────────────────────────── -->
    <q-banner v-if="settingsStore.error" rounded class="bg-red-1 text-red-9 q-mb-md">
      <template v-slot:avatar>
        <q-icon name="error" color="red" />
      </template>
      {{ settingsStore.error }}
    </q-banner>

    <!-- ─── CARDS PER CATEGORIA ─────────────────────── -->
    <div v-for="cat in orderedCategories" :key="cat" class="q-mb-md">
      <q-card flat bordered>
        <q-expansion-item
          :label="cat"
          :icon="categoryIcon(cat)"
          header-class="text-weight-bold text-primary bg-blue-1"
          default-opened
          expand-icon-class="text-primary"
        >
          <q-separator />
          <q-card-section>
            <div
              v-for="setting in settingsStore.groupedByCategory[cat]"
              :key="setting.key"
              class="row items-center q-mb-md"
            >
              <!-- Label + Info -->
              <div class="col-12 col-sm-6 q-pr-md">
                <div class="text-subtitle2 text-grey-9">{{ setting.description }}</div>
                <div class="text-caption text-grey-5" style="font-family: monospace;">
                  {{ setting.key }}
                </div>
              </div>

              <!-- Input Numerico -->
              <div class="col-12 col-sm-3">
                <q-input
                  :model-value="setting.value"
                  @update:model-value="(v) => settingsStore.updateLocalValue(setting.key, v)"
                  type="number"
                  outlined
                  dense
                  :suffix="getSuffix(cat)"
                  input-class="text-right text-weight-medium"
                  style="max-width: 160px;"
                />
              </div>

              <!-- Slider (solo per tempi, range 5–120 min) -->
              <div v-if="isTimeSetting(cat)" class="col-12 col-sm-3 q-pl-md">
                <q-slider
                  :model-value="Number(setting.value)"
                  @update:model-value="(v) => settingsStore.updateLocalValue(setting.key, v)"
                  :min="5"
                  :max="120"
                  :step="5"
                  color="primary"
                  label
                  :label-value="setting.value + ' min'"
                />
              </div>

              <!-- Slider per posti (range 0–20) -->
              <div v-if="isCapacitySetting(cat)" class="col-12 col-sm-3 q-pl-md">
                <q-slider
                  :model-value="Number(setting.value)"
                  @update:model-value="(v) => settingsStore.updateLocalValue(setting.key, v)"
                  :min="0"
                  :max="20"
                  :step="1"
                  color="teal"
                  label
                  :label-value="setting.value + ' posti'"
                />
              </div>
            </div>
          </q-card-section>
        </q-expansion-item>
      </q-card>
    </div>

    <!-- ─── INFO FOOTER ─────────────────────────────── -->
    <q-card v-if="settingsStore.settings.length > 0" flat bordered class="q-mt-lg bg-grey-1">
      <q-card-section>
        <div class="row items-center">
          <q-icon name="info" color="blue-grey" class="q-mr-sm" />
          <span class="text-caption text-blue-grey">
            <strong>Passeggeri Utili per Van</strong> = Posti totali ({{ getVal('van_total_seats') }})
            − Autista ({{ getVal('van_driver_seats') }})
            − Guida ({{ getVal('van_guide_seats') }})
            = <strong class="text-primary">{{ computedUsefulSeats }}</strong> passeggeri
          </span>
        </div>
      </q-card-section>
    </q-card>

  </q-page>
</template>

<script>
import { defineComponent, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useSettingsStore } from 'src/stores/settings-store'

export default defineComponent({
  name: 'SettingsPage',

  setup() {
    const $q = useQuasar()
    const settingsStore = useSettingsStore()

    onMounted(async () => {
      if (settingsStore.settings.length === 0) {
        await settingsStore.fetchSettings()
      }
    })

    // ── Categorie ordinate ──
    const orderedCategories = computed(() => {
      const order = settingsStore.categoryOrder
      const available = Object.keys(settingsStore.groupedByCategory)
      // Categorie in ordine definito + eventuali extra non previste
      const ordered = order.filter(c => available.includes(c))
      const extras = available.filter(c => !order.includes(c))
      return [...ordered, ...extras]
    })

    // ── Icone per categoria ──
    function categoryIcon(cat) {
      if (cat.includes('Capienze')) return 'directions_bus'
      if (cat.includes('Base'))    return 'timer'
      if (cat.includes('Tratto A')) return 'kayaking'
      if (cat.includes('Tratto B')) return 'water'
      return 'settings'
    }

    // ── Suffisso unità di misura ──
    function getSuffix(cat) {
      if (cat.includes('min'))      return 'min'
      if (cat.includes('Capienze')) return 'posti'
      return ''
    }

    function isTimeSetting(cat) {
      return cat.toLowerCase().includes('min')
    }

    function isCapacitySetting(cat) {
      return cat.toLowerCase().includes('capienz')
    }

    // ── Getter helper per il footer ──
    function getVal(key) {
      return settingsStore.getSetting(key) || '0'
    }

    const computedUsefulSeats = computed(() => {
      const total  = settingsStore.getSettingNum('van_total_seats')
      const driver = settingsStore.getSettingNum('van_driver_seats')
      const guide  = settingsStore.getSettingNum('van_guide_seats')
      return total - driver - guide
    })

    // ── Salvataggio ──
    async function saveSettings() {
      try {
        await settingsStore.saveAllSettings()
        $q.notify({
          type: 'positive',
          message: 'Impostazioni salvate con successo!',
          icon: 'check_circle',
          position: 'top',
          timeout: 2500,
        })
      } catch (err) {
        $q.notify({
          type: 'negative',
          message: 'Errore durante il salvataggio.',
          caption: err.message || 'Controlla la connessione al backend.',
          icon: 'error',
          position: 'top',
          timeout: 4000,
        })
      }
    }

    return {
      settingsStore,
      orderedCategories,
      categoryIcon,
      getSuffix,
      isTimeSetting,
      isCapacitySetting,
      getVal,
      computedUsefulSeats,
      saveSettings,
    }
  },
})
</script>
