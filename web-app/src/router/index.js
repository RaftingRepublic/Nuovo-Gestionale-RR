import { defineRouter } from '#q-app/wrappers'
import {
  createRouter,
  createMemoryHistory,
  createWebHistory,
  createWebHashHistory,
} from 'vue-router'
import routes from './routes'
import { useAuthStore } from 'src/stores/auth-store'

/*
 * If not building with SSR mode, you can
 * directly export the Router instantiation;
 *
 * The function below can be async too; either use
 * async/await or return a Promise which resolves
 * with the Router instance.
 */

export default defineRouter(function (/* { store, ssrContext } */) {
  const createHistory = process.env.SERVER
    ? createMemoryHistory
    : process.env.VUE_ROUTER_MODE === 'history'
      ? createWebHistory
      : createWebHashHistory

  const Router = createRouter({
    scrollBehavior: () => ({ left: 0, top: 0 }),
    routes,

    // Leave this as is and make changes in quasar.conf.js instead!
    // quasar.conf.js -> build -> vueRouterMode
    // quasar.conf.js -> build -> publicPath
    history: createHistory(process.env.VUE_ROUTER_BASE),
  })

  // ─────────────────────────────────────────────────────────
  // NAVIGATION GUARD — Il "Buttafuori"
  // Controlla ogni navigazione PRIMA che avvenga.
  // ─────────────────────────────────────────────────────────
  Router.beforeEach((to, from, next) => {
    // Istanziamo lo store QUI DENTRO per evitare l'errore
    // "getActivePinia() was called but there was no active Pinia"
    const authStore = useAuthStore()

    // Ripristina il token dal localStorage (se presente)
    authStore.loadSession()

    const isAuthenticated = authStore.isAuthenticated
    const requiresAuth = to.matched.some((record) => record.meta.requiresAuth)

    // ─── ANTI-LOOP: Operatore autenticato su area pubblica → admin ───
    // Se l'utente è loggato e atterra sulla root "/" o "/consenso" (Kiosk),
    // lo redirigiamo all'area admin. Il Kiosk resta accessibile da browser
    // non autenticati (tablet clienti).
    const publicPaths = ['/', '/consenso']
    if (isAuthenticated && publicPaths.includes(to.path)) {
      next('/admin/operativo')
      return
    }

    if (requiresAuth && !isAuthenticated) {
      // Rotta protetta, utente NON autenticato → manda al login
      next('/login')
    } else if (to.path === '/login' && isAuthenticated) {
      // Utente già autenticato che prova ad andare su /login → manda alla home admin
      next('/admin/operativo')
    } else {
      // Tutto ok, procedi
      next()
    }
  })

  return Router
})
