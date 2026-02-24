const routes = [
  // Login — rotta standalone, SENZA MainLayout (niente sidebar/header)
  {
    path: '/login',
    component: () => import('pages/LoginPage.vue'),
  },

  // Modulo Pubblico — Consenso Informato (NO auth richiesta)
  // Questa è la LANDING PAGE del Kiosk tablet
  {
    path: '/',
    component: () => import('layouts/PublicLayout.vue'),
    children: [
      { path: '', redirect: '/consenso' },
      { path: 'consenso', component: () => import('pages/public/ConsentFormPage.vue') },
    ],
  },

  {
    path: '/admin',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // Home / Dashboard → redirect to Operativo (default)
      { path: '', redirect: '/admin/operativo' },

      // Flusso Registrazione (Scanner)
      { path: 'scanner/:id?', component: () => import('pages/ScannerPage.vue') },

      // Archivio Consensi / Registrazioni  ← PONTE Strada A → Strada B
      { path: 'registrazioni', component: () => import('pages/admin/RegistrationsPage.vue') },

      // Gestione Prenotazioni
      { path: 'prenotazioni', component: () => import('pages/ReservationsPage.vue') },

      // Gestione Risorse (Staff, Flotta, Slot)
      { path: 'risorse', component: () => import('pages/ResourcesPage.vue') },

      // Pannello Variabili (Tempi e Capienze)
      { path: 'impostazioni', component: () => import('pages/admin/SettingsPage.vue') },

      // FASE 1: Due ambienti separati che caricano lo stesso componente
      // Calendario Operativo
      { path: 'operativo', component: () => import('pages/PlanningPage.vue') },

      // Segreteria (POS)
      { path: 'segreteria', component: () => import('pages/PlanningPage.vue') },

      // Redirect legacy per backward-compatibility
      { path: 'pianificazione', redirect: '/admin/operativo' },
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue')
  }
]

export default routes
