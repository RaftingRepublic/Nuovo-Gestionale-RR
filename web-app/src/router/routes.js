const routes = [
  // Login — rotta standalone, SENZA MainLayout (niente sidebar/header)
  {
    path: '/login',
    component: () => import('pages/LoginPage.vue'),
  },

  // Modulo Pubblico — Consenso Informato (NO auth richiesta)
  {
    path: '/consenso',
    component: () => import('layouts/PublicLayout.vue'),
    children: [
      { path: '', component: () => import('pages/public/ConsentFormPage.vue') },
    ],
  },

  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      // Home / Dashboard
      // Redirect root to Planning
      { path: '', redirect: '/pianificazione' },

      // Flusso Registrazione (Scanner)
      { path: 'scanner/:id?', component: () => import('pages/ScannerPage.vue') },

      // Archivio Registrazioni
      { path: 'registrazioni', component: () => import('pages/RegistrationPage.vue') },

      // Gestione Prenotazioni (NUOVO)
      { path: 'prenotazioni', component: () => import('pages/ReservationsPage.vue') },


      // Gestione Risorse (Staff, Flotta, Slot)
      { path: 'risorse', component: () => import('pages/ResourcesPage.vue') },

      // NUOVO: Pianificazione Attività (Calendario Operativo)
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
