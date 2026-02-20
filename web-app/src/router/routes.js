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
    // TODO: Riabilitare in produzione → meta: { requiresAuth: true },
    children: [
      // Home / Dashboard → redirect to Planning
      { path: '', redirect: '/admin/pianificazione' },

      // Flusso Registrazione (Scanner)
      { path: 'scanner/:id?', component: () => import('pages/ScannerPage.vue') },

      // Archivio Consensi / Registrazioni  ← PONTE Strada A → Strada B
      { path: 'registrazioni', component: () => import('pages/admin/RegistrationsPage.vue') },

      // Gestione Prenotazioni
      { path: 'prenotazioni', component: () => import('pages/ReservationsPage.vue') },

      // Gestione Risorse (Staff, Flotta, Slot)
      { path: 'risorse', component: () => import('pages/ResourcesPage.vue') },

      // Pianificazione Attività (Calendario Operativo)
      { path: 'pianificazione', component: () => import('pages/PlanningPage.vue') }
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
