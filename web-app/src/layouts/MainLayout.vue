<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />
        <q-toolbar-title>Rafting Republic • Gestionale</q-toolbar-title>
        <div class="text-caption">Quasar v{{ $q.version }}</div>
      </q-toolbar>
    </q-header>

    <q-drawer v-model="leftDrawerOpen" show-if-above bordered>
      <q-list padding>
        <q-item-label header>Menu Principale</q-item-label>



        <q-item clickable v-ripple to="/scanner">
          <q-item-section avatar><q-icon name="document_scanner" /></q-item-section>
          <q-item-section>Nuova registrazione</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/registrazioni">
          <q-item-section avatar><q-icon name="assignment" /></q-item-section>
          <q-item-section>Registrazioni</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/prenotazioni">
          <q-item-section avatar><q-icon name="book_online" /></q-item-section>
          <q-item-section>Prenotazioni</q-item-section>
        </q-item>

        <q-separator class="q-my-md" />
        <q-item-label header>Amministrazione</q-item-label>

        <q-item clickable v-ripple to="/risorse">
          <q-item-section avatar><q-icon name="groups" /></q-item-section>
          <q-item-section>Staff & Risorse</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/pianificazione">
          <q-item-section avatar><q-icon name="calendar_month" /></q-item-section>
          <q-item-section>Pianificazione</q-item-section>
        </q-item>

        <!-- Spacer per spingere il logout in fondo -->
        <q-space />

        <q-separator class="q-my-md" />

        <q-item clickable v-ripple @click="onLogout" class="text-red-4">
          <q-item-section avatar><q-icon name="logout" color="red-4" /></q-item-section>
          <q-item-section>Esci</q-item-section>
        </q-item>

      </q-list>
    </q-drawer>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { defineComponent, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from 'src/stores/auth-store'

export default defineComponent({
  name: 'MainLayout',
  setup () {
    const leftDrawerOpen = ref(false)
    const toggleLeftDrawer = () => { leftDrawerOpen.value = !leftDrawerOpen.value }

    const router = useRouter()
    const authStore = useAuthStore()

    function onLogout () {
      authStore.logout()
      router.push('/login')
    }

    return { leftDrawerOpen, toggleLeftDrawer, onLogout }
  }
})
</script>
