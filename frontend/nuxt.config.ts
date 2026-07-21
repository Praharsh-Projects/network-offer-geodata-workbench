export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
  devtools: { enabled: false },
  css: ['~/assets/scss/main.scss'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000',
    },
  },
  typescript: {
    strict: true,
    typeCheck: true,
  },
  app: {
    head: {
      title: 'Network Offer Geodata Workbench',
      meta: [
        {
          name: 'description',
          content: 'Synthetic network corridor evaluation using WFS, WMS, and reproducible geometry processing.',
        },
      ],
    },
  },
})
