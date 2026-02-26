<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated class="bg-primary">
      <q-toolbar>
        <q-btn flat dense round icon="menu" aria-label="Menu" @click="toggleLeftDrawer" />
        <img src="/logo.png" style="height: 32px; object-fit: contain;" alt="Rafting Republic" class="q-ml-sm q-mr-sm" />
        <q-toolbar-title>Rafting Republic</q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      side="left"
      bordered
      behavior="mobile"
    >
      <q-list padding>
        <q-item-label header class="text-weight-bold text-grey-8">Operativo</q-item-label>

        <q-item clickable v-ripple to="/admin/operativo" active-class="text-primary bg-blue-1" @click="leftDrawerOpen = false">
          <q-item-section avatar><q-icon name="event" /></q-item-section>
          <q-item-section>Calendario Operativo</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/admin/timeline" active-class="text-primary bg-blue-1" @click="leftDrawerOpen = false">
          <q-item-section avatar><q-icon name="view_timeline" /></q-item-section>
          <q-item-section>Timeline Operativa</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/admin/board" active-class="text-primary bg-blue-1" @click="leftDrawerOpen = false">
          <q-item-section avatar><q-icon name="view_column" /></q-item-section>
          <q-item-section>Lavagna Operativa</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/admin/segreteria" active-class="text-primary bg-blue-1" @click="leftDrawerOpen = false">
          <q-item-section avatar><q-icon name="point_of_sale" /></q-item-section>
          <q-item-section>Segreteria (POS)</q-item-section>
        </q-item>

        <q-separator class="q-my-md" />
        <q-item-label header class="text-weight-bold text-grey-8">Consensi &amp; Registrazioni</q-item-label>

        <q-item clickable v-ripple to="/admin/registrazioni" active-class="text-primary bg-blue-1" @click="leftDrawerOpen = false">
          <q-item-section avatar><q-icon name="folder_shared" /></q-item-section>
          <q-item-section>Archivio Consensi</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/admin/scanner" active-class="text-primary bg-blue-1" @click="leftDrawerOpen = false">
          <q-item-section avatar><q-icon name="document_scanner" /></q-item-section>
          <q-item-section>Nuova Registrazione</q-item-section>
        </q-item>

        <q-separator class="q-my-md" />
        <q-item-label header class="text-weight-bold text-grey-8">Amministrazione</q-item-label>

        <q-item clickable v-ripple to="/admin/risorse" active-class="text-primary bg-blue-1" @click="leftDrawerOpen = false">
          <q-item-section avatar><q-icon name="groups" /></q-item-section>
          <q-item-section>Staff &amp; Risorse</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/admin/impostazioni" active-class="text-primary bg-blue-1" @click="leftDrawerOpen = false">
          <q-item-section avatar><q-icon name="tune" /></q-item-section>
          <q-item-section>Pannello Variabili</q-item-section>
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
