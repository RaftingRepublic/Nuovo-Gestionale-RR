<template>
  <q-page class="q-pa-md bg-blue-grey-1">
    
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="text-h5 text-weight-bold text-blue-grey-9">Staff & Risorse</div>
        <div class="text-caption text-grey-7">Gestione operativa: Guide, Autisti e Parco Mezzi.</div>
      </div>
    </div>

    <q-card class="shadow-2 fit-height-card my-rounded overflow-hidden row no-wrap">
      
      <div class="col-auto border-right bg-white column" style="width: 250px">
        <div class="q-pa-md bg-blue-50 text-weight-bold text-blue-9">CATEGORIE</div>
        
        <q-tabs vertical v-model="activeCategory" class="text-grey-7 col" active-bg-color="blue-1" active-color="primary" indicator-color="primary">
          <q-tab name="STAFF" icon="groups" label="Personale" class="justify-start q-pl-md" />
          <q-tab name="FLEET" icon="sailing" label="Flotta & Mezzi" class="justify-start q-pl-md" />
        </q-tabs>

        <div class="q-pa-md border-top">
          <q-btn v-if="activeCategory === 'STAFF'" unelevated color="primary" icon="person_add" label="Nuovo Staff" class="full-width" @click="openDialog('STAFF')" />
          <q-btn v-if="activeCategory === 'FLEET'" unelevated color="secondary" icon="add" label="Nuovo Mezzo" class="full-width" @click="openDialog('FLEET')" />
        </div>
      </div>

      <div class="col-3 border-right bg-grey-1 column" style="min-width: 280px">
        <div class="q-pa-sm q-px-md text-caption text-grey-6 bg-grey-2 border-bottom row justify-between items-center">
          <span>ELENCO {{ activeCategory }}</span>
          <q-badge color="grey-4" text-color="black">{{ activeCategory==='STAFF' ? store.staffList.length : store.fleetList.length }}</q-badge>
        </div>
        
        <q-scroll-area class="col">
          <q-list separator>
            
            <template v-if="activeCategory === 'STAFF'">
              <q-item v-for="m in store.staffList" :key="m.id" clickable :active="store.selectedStaffId === m.id" active-class="bg-white border-left-active" class="resource-item" @click="selectResource(m.id)">
                <q-item-section avatar>
                  <q-avatar :color="getAvatarColor(m)" text-color="white" size="sm" font-size="14px">{{ m.name.charAt(0) }}</q-avatar>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ m.name }}</q-item-label>
                  <q-item-label caption class="ellipsis">{{ getRoleLabel(m) }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn flat round dense icon="delete" color="grey-4" size="sm" @click.stop="deleteItem('STAFF', m.id)" />
                </q-item-section>
              </q-item>
            </template>

            <template v-if="activeCategory === 'FLEET'">
              <q-item v-for="f in store.fleetList" :key="f.id" clickable :active="store.selectedStaffId === f.id" active-class="bg-white border-left-active-orange" class="resource-item" @click="selectResource(f.id)">
                <q-item-section avatar>
                  <q-icon :name="getFleetIcon(f.type)" color="grey-7" size="sm" />
                </q-item-section>
                <q-item-section>
                  <q-item-label class="text-weight-bold">{{ f.name }}</q-item-label>
                  <q-item-label caption>Cap: {{ f.capacity }} | P: {{ f.priority }}</q-item-label>
                </q-item-section>
                <q-item-section side>
                  <q-btn flat round dense icon="delete" color="grey-4" size="sm" @click.stop="deleteItem('FLEET', f.id)" />
                </q-item-section>
              </q-item>
            </template>

          </q-list>
        </q-scroll-area>
      </div>

      <div class="col bg-white q-pa-lg scroll">
        <div v-if="selectedRes" class="column h-full">
          
          <div class="row items-center q-mb-lg bg-grey-1 q-pa-md rounded-borders">
            <q-avatar size="64px" :color="activeCategory==='STAFF' ? getAvatarColor(selectedRes) : 'blue-grey'" text-color="white" class="q-mr-md shadow-2">
              {{ selectedRes.name.charAt(0) }}
            </q-avatar>
            <div class="col">
              <div class="text-h5 text-weight-bold no-margin">{{ selectedRes.name }}</div>
              
              <div v-if="activeCategory === 'STAFF'" class="row q-gutter-xs q-mt-xs">
                <q-badge v-if="selectedRes.is_guide" color="teal" class="q-py-xs">Guida {{ formatLevel(selectedRes.guide_level) }}</q-badge>
                <q-badge v-if="selectedRes.is_driver" color="orange" class="q-py-xs">Autista</q-badge>
                <q-badge v-if="selectedRes.is_photographer" color="purple" class="q-py-xs">Foto</q-badge>
              </div>
              
              <div v-else class="text-subtitle2 text-grey-7 q-mt-xs">
                {{ selectedRes.type === 'RAFT' ? 'Gommone' : (selectedRes.type === 'VAN' ? 'Furgone' : 'Carrello') }} 
                • Capienza: <b>{{ selectedRes.capacity }}</b>
                <span v-if="selectedRes.has_tow_hitch" class="text-green q-ml-sm text-weight-bold">✔ Gancio</span>
              </div>
            </div>
          </div>

          <div class="text-subtitle1 text-weight-bold text-grey-9 q-mb-sm">Calendario & Manutenzione</div>
          
          <q-card bordered flat class="bg-white col overflow-hidden column">
            <q-tabs v-model="avMode" dense class="text-grey-7 bg-grey-2" active-color="primary" align="justify" indicator-color="primary">
              <q-tab name="CALENDAR" label="Calendario (Ferie / Manutenzione)" icon="event" />
            </q-tabs>
            <q-separator />
            
            <q-tab-panels v-model="avMode" animated class="col scroll q-pa-none">
              
              <q-tab-panel name="CALENDAR" class="q-pa-md">
                <div class="row q-col-gutter-lg h-full">
                  <div class="col-auto">
                    <q-date 
                      v-model="calendarDates" 
                      multiple range minimal flat bordered 
                      :events="calendarEvents"
                      :event-color="getEventColor"
                      today-btn
                      class="shadow-1"
                    />
                    <div class="row justify-center q-gutter-md q-mt-sm">
                      <div class="row items-center text-caption"><div class="circle bg-green q-mr-xs"></div> Extra</div>
                      <div class="row items-center text-caption"><div class="circle bg-red q-mr-xs"></div> Off/Manut.</div>
                    </div>
                  </div>

                  <div class="col column justify-center">
                    <div class="bg-grey-1 q-pa-md rounded-borders border-grey">
                      <div class="text-weight-bold text-grey-9 q-mb-sm">Gestione Giornata</div>
                      <div class="text-caption text-grey-6 q-mb-md">Seleziona i giorni sul calendario per applicare modifiche.</div>

                      <q-btn-group spread unelevated class="q-mb-md shadow-1">
                        <q-btn 
                          :color="avType === 'AVAILABLE' ? 'positive' : 'white'" 
                          :text-color="avType === 'AVAILABLE' ? 'white' : 'grey-8'"
                          label="Disponibile" 
                          icon="check_circle"
                          @click="avType = 'AVAILABLE'"
                        />
                        <q-btn 
                          :color="avType === 'UNAVAILABLE' ? 'negative' : 'white'" 
                          :text-color="avType === 'UNAVAILABLE' ? 'white' : 'grey-8'"
                          label="Non Disp / Off" 
                          icon="block"
                          @click="avType = 'UNAVAILABLE'"
                        />
                      </q-btn-group>

                      <div class="row q-col-gutter-sm q-mb-sm">
                        <div class="col-6"><q-input v-model.number="timeStart" label="Dalle" type="number" outlined dense suffix=":00" bg-color="white" /></div>
                        <div class="col-6"><q-input v-model.number="timeEnd" label="Alle" type="number" outlined dense suffix=":00" bg-color="white" /></div>
                      </div>

                      <q-input v-model="avNotes" label="Note (opzionale)" placeholder="Es. Motore rotto, Ferie" outlined dense bg-color="white" class="q-mb-md" />

                      <q-btn class="full-width" color="primary" label="Salva Modifiche" icon="save" @click="saveSpecificDates" :loading="store.loading" />
                    </div>
                  </div>
                </div>
              </q-tab-panel>

            </q-tab-panels>
          </q-card>

        </div>
        <div v-else class="flex flex-center h-full text-grey-5 column">
          <q-icon name="touch_app" size="80px" color="grey-3" />
          <div class="text-h6 q-mt-md text-grey-4">Seleziona una risorsa dall'elenco</div>
        </div>
      </div>

    </q-card>

    <q-dialog v-model="dialog.open" persistent>
      <q-card style="min-width: 450px" class="my-rounded">
        <q-card-section class="bg-primary text-white row items-center justify-between q-py-sm">
          <div class="text-h6">{{ dialog.type === 'STAFF' ? 'Aggiungi Personale' : 'Aggiungi Mezzo' }}</div>
          <q-btn flat round dense icon="close" v-close-popup />
        </q-card-section>
        <q-card-section class="q-pt-md">
          <q-form v-if="dialog.type === 'STAFF'" @submit="submitStaff" class="q-gutter-md">
            <q-input v-model="formStaff.name" label="Nome" outlined dense :rules="[val => !!val || 'Req']" />
            <div class="text-weight-bold">Ruoli</div>
            <div class="row"><q-checkbox v-model="formStaff.is_guide" label="Guida" class="col-4" /><q-checkbox v-model="formStaff.is_driver" label="Autista" class="col-4" /><q-checkbox v-model="formStaff.is_photographer" label="Foto" class="col-4" /></div>
            <div v-if="formStaff.is_guide"><q-select v-model="formStaff.guide_level" :options="['3_LIV', '4_LIV', 'TRIP_LEADER']" label="Livello" outlined dense /></div>
            <div class="row justify-end q-mt-lg"><q-btn label="Salva" type="submit" color="primary" /></div>
          </q-form>
          <q-form v-if="dialog.type === 'FLEET'" @submit="submitFleet" class="q-gutter-md">
            <q-select v-model="formFleet.type" :options="[{label:'Gommone', value:'RAFT'}, {label:'Furgone', value:'VAN'}, {label:'Carrello', value:'TRAILER'}]" label="Tipo" outlined dense />
            <q-input v-model="formFleet.name" label="Nome" outlined dense />
            <div class="row q-col-gutter-sm"><div class="col-6"><q-input v-model.number="formFleet.capacity" label="Capienza" type="number" outlined dense /></div><div class="col-6"><q-input v-model.number="formFleet.priority" label="Priorità" type="number" outlined dense /></div></div>
            <q-checkbox v-if="formFleet.type === 'VAN'" v-model="formFleet.has_tow_hitch" label="Gancio Traino" color="orange" />
            <div class="row justify-end q-mt-lg"><q-btn label="Salva" type="submit" color="secondary" /></div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useResourceStore } from 'stores/resource-store'
import { useQuasar } from 'quasar'

const store = useResourceStore()
const $q = useQuasar()

// Layout
const activeCategory = ref('STAFF')
const avMode = ref('CALENDAR') // Default su calendario per gestire eccezioni
const dialog = reactive({ open: false, type: null })

const selectedRes = computed(() => store.selectedResource)

// Logic Calendar Events
const calendarEvents = computed(() => {
  // Mappa le regole della risorsa corrente in date colorate
  const events = {}
  if (!store.currentResourceRules) return []
  
  store.currentResourceRules.forEach(r => {
    if (r.specific_date) {
      // YYYY-MM-DD format for Quasar
      const dateKey = r.specific_date.replace(/-/g, '/')
      // Verde se Disponibile, Rosso se Unavailable
      events[dateKey] = (r.type === 'UNAVAILABLE') ? 'red' : 'green'
    }
  })
  return Object.keys(events)
})

function getEventColor(date) {
  // Recupera il colore dalla mappa calcolata sopra
  const dateKey = date // Quasar passa YYYY/MM/DD
  const rule = store.currentResourceRules.find(r => r.specific_date === dateKey.replace(/\//g, '-'))
  if (!rule) return 'grey'
  return rule.type === 'UNAVAILABLE' ? 'red' : 'green'
}

// Data Models
const calendarDates = ref(null)
const timeStart = ref(9)
const timeEnd = ref(18)
const avType = ref('UNAVAILABLE') // Default per calendario (utile per ferie/manutenzione)
const avNotes = ref('')

const formStaff = reactive({ name: '', is_guide: false, is_driver: false, is_photographer: false, guide_level: null, guide_skills: [] })
const formFleet = reactive({ type: 'RAFT', name: '', capacity: 8, priority: 1, has_tow_hitch: false })

onMounted(() => { store.fetchStaff(); store.fetchFleet() })

// Helpers
function getAvatarColor(m) { return m.is_guide ? 'teal' : (m.is_driver ? 'orange' : 'purple') }
function getRoleLabel(m) { return (m.is_guide?'Guida ':'')+(m.is_driver?'Autista ':'')+(m.is_photographer?'Foto':'') }
function getFleetIcon(t) { return t==='RAFT'?'sailing':(t==='VAN'?'airport_shuttle':'rv_hookup') }
function formatLevel(lvl) { return lvl ? lvl.replace('_LIV', '°') : '' }

// Actions
function openDialog(type) { dialog.type = type; dialog.open = true; if(type==='STAFF')formStaff.name=''; if(type==='FLEET')formFleet.name=''; }
async function submitStaff() { await store.addStaff({...formStaff}); dialog.open = false; $q.notify('Staff aggiunto') }
async function submitFleet() { await store.addFleet({...formFleet}); dialog.open = false; $q.notify('Mezzo aggiunto') }

async function selectResource(id) {
  store.selectStaff(id) // Funziona anche per Fleet grazie al getter smart
  // Fetch delle regole specifiche per colorare il calendario
  await store.fetchResourceRules(id)
}

async function deleteItem(type, id) {
  if(!confirm('Eliminare definitivamente?')) return
  if(type==='STAFF') await store.deleteStaff(id)
  else await store.deleteFleet(id)
  $q.notify('Eliminato')
}

// Logic Availability
// Logic Availability
async function saveSpecificDates() {
  if (!selectedRes.value || !calendarDates.value) return
  const dates = extractDates(calendarDates.value)
  try {
    await store.addAvailability({
      staff_id: selectedRes.value.id,
      mode: 'SPECIFIC', specific_dates: dates,
      start_hour: Number(timeStart.value), end_hour: Number(timeEnd.value),
      type: avType.value, // AVAILABLE o UNAVAILABLE
      notes: avNotes.value
    })
    $q.notify({type:'positive', message: 'Eccezioni salvate'})
    calendarDates.value = null
    avNotes.value = ''
  } catch(e) { console.error(e) }
}

function extractDates(val) {
  let res = []
  if (!val) return []
  if (typeof val === 'string') res.push(val)
  else if (Array.isArray(val)) val.forEach(v => { if (typeof v === 'string') res.push(v); else if (v.from) res = res.concat(expandRange(v.from, v.to)) })
  else if (val.from) res = res.concat(expandRange(val.from, val.to))
  return [...new Set(res)].map(d => d.replace(/\//g, '-'))
}
function expandRange(s, e) {
  const arr = []; const c = new Date(s.replace(/-/g, '/')); const end = new Date(e.replace(/-/g, '/'))
  while (c <= end) { arr.push(c.toISOString().split('T')[0]); c.setDate(c.getDate()+1) }
  return arr
}
</script>

<style scoped>
.my-rounded { border-radius: 12px; }
.fit-height-card { height: calc(100vh - 100px); min-height: 500px; }
.border-right { border-right: 1px solid #e0e0e0; }
.border-left-active { border-left: 4px solid var(--q-primary); }
.border-left-active-orange { border-left: 4px solid var(--q-warning); }
.border-bottom { border-bottom: 1px solid #eee; }
.border-grey { border: 1px solid #ddd; }
.border-top { border-top: 1px solid #e0e0e0; }
.h-full { height: 100%; }
.resource-item { transition: background 0.2s; }
.circle { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
</style>