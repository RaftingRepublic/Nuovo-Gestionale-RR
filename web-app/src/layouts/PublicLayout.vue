<template>
  <q-layout view="hHh lpR fFf">
    <q-header class="public-header">
      <q-toolbar>
        <q-toolbar-title class="public-brand">
          <img src="/logo.png" style="height: 28px; object-fit: contain;" alt="Rafting Republic" class="q-mr-sm" />
          Rafting Republic
        </q-toolbar-title>
      </q-toolbar>
    </q-header>

    <q-page-container>
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup>
// Layout pubblico — nessuna logica necessaria
</script>

<style lang="scss" scoped>
.public-header {
  background: linear-gradient(135deg, #1e40af, #2563eb);
}
.public-brand {
  font-weight: 700;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
}
</style>
