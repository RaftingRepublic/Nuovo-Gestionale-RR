<template>
  <q-layout>
    <q-page-container>
      <q-page class="login-page flex flex-center">
        <!-- Sfondo decorativo -->
        <div class="login-bg-circles">
          <div class="circle circle-1"></div>
          <div class="circle circle-2"></div>
          <div class="circle circle-3"></div>
        </div>

        <q-card class="login-card" flat bordered>
          <!-- Header con icona -->
          <q-card-section class="login-header text-center">
            <q-icon name="lock" class="login-icon" />
            <h1 class="login-title">Area Riservata</h1>
            <p class="login-subtitle">Rafting Republic</p>
          </q-card-section>

          <q-separator inset />

          <!-- Form -->
          <q-card-section class="q-pt-lg">
            <q-form @submit.prevent="onLogin" class="q-gutter-md">
              <q-input
                v-model="username"
                label="Username"
                outlined
                dense
                :disable="loading"
                autocomplete="username"
              >
                <template v-slot:prepend>
                  <q-icon name="person" color="grey-7" />
                </template>
              </q-input>

              <q-input
                v-model="password"
                label="Password"
                outlined
                dense
                :type="showPassword ? 'text' : 'password'"
                :disable="loading"
                autocomplete="current-password"
              >
                <template v-slot:prepend>
                  <q-icon name="vpn_key" color="grey-7" />
                </template>
                <template v-slot:append>
                  <q-icon
                    :name="showPassword ? 'visibility_off' : 'visibility'"
                    class="cursor-pointer"
                    @click="showPassword = !showPassword"
                  />
                </template>
              </q-input>

              <q-btn
                type="submit"
                label="Accedi"
                class="login-btn full-width"
                unelevated
                no-caps
                size="lg"
                :loading="loading"
                :disable="loading || !username || !password"
              />
            </q-form>
          </q-card-section>

          <!-- Footer -->
          <q-card-section class="login-footer text-center q-pt-none">
            <p class="text-caption text-grey-6">
              Gestionale interno &middot; Accesso riservato al personale
            </p>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from 'src/stores/auth-store'

const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)

async function onLogin() {
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    $q.notify({
      type: 'positive',
      message: `Benvenuto, ${authStore.userName}!`,
      icon: 'check_circle',
      position: 'top',
      timeout: 2000,
    })
    router.push('/')
  } catch (err) {
    const message =
      err.response?.data?.message || 'Credenziali errate. Riprova.'
    $q.notify({
      type: 'negative',
      message,
      icon: 'error',
      position: 'top',
      timeout: 3500,
    })
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
/* ─── Pagina ─── */
.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
  position: relative;
  overflow: hidden;
}

/* ─── Cerchi decorativi di sfondo ─── */
.login-bg-circles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.07;
}
.circle-1 {
  width: 500px;
  height: 500px;
  background: #3b82f6;
  top: -120px;
  right: -100px;
  animation: float 8s ease-in-out infinite;
}
.circle-2 {
  width: 350px;
  height: 350px;
  background: #06b6d4;
  bottom: -80px;
  left: -60px;
  animation: float 10s ease-in-out infinite reverse;
}
.circle-3 {
  width: 200px;
  height: 200px;
  background: #8b5cf6;
  top: 40%;
  left: 60%;
  animation: float 12s ease-in-out infinite 2s;
}
@keyframes float {
  0%,
  100% {
    transform: translateY(0) scale(1);
  }
  50% {
    transform: translateY(-30px) scale(1.05);
  }
}

/* ─── Card ─── */
.login-card {
  width: 100%;
  max-width: 420px;
  z-index: 1;
  border-radius: 16px;
  background: rgba(30, 41, 59, 0.85);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

/* ─── Header ─── */
.login-header {
  padding-top: 32px;
  padding-bottom: 16px;
}
.login-icon {
  font-size: 48px;
  color: #3b82f6;
  background: rgba(59, 130, 246, 0.12);
  border-radius: 50%;
  padding: 16px;
  margin-bottom: 12px;
}
.login-title {
  font-size: 1.4rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  color: #f1f5f9;
  margin: 0;
  line-height: 1.3;
}
.login-subtitle {
  font-size: 0.95rem;
  font-weight: 400;
  color: #64748b;
  margin: 4px 0 0;
}

/* ─── Input overrides (dark theme) ─── */
.login-card :deep(.q-field__control) {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 10px;
}
.login-card :deep(.q-field--outlined .q-field__control:before) {
  border-color: rgba(255, 255, 255, 0.1);
}
.login-card :deep(.q-field--outlined .q-field__control:hover:before) {
  border-color: rgba(59, 130, 246, 0.4);
}
.login-card :deep(.q-field--outlined.q-field--focused .q-field__control:after) {
  border-color: #3b82f6;
}
.login-card :deep(.q-field__label) {
  color: #94a3b8;
}
.login-card :deep(.q-field__native),
.login-card :deep(.q-field__input) {
  color: #e2e8f0;
}

/* ─── Bottone ─── */
.login-btn {
  margin-top: 8px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  font-weight: 600;
  letter-spacing: 0.03em;
  border-radius: 10px;
  height: 48px;
  transition: all 0.25s ease;
}
.login-btn:hover {
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  box-shadow: 0 8px 24px -4px rgba(59, 130, 246, 0.4);
  transform: translateY(-1px);
}
.login-btn:active {
  transform: translateY(0);
}

/* ─── Footer ─── */
.login-footer p {
  margin: 0;
}
</style>
