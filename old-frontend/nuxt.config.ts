// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
    ssr: false,
    devtools: {enabled: true},
    modules: ["@nuxt/ui"],
    compatibilityDate: "2025-01-05",
    nitro: {
        experimental: {
            tasks: true,
        },
        scheduledTasks: {
            // Run `cms:update` task every minute
            '0 1 * * *': ['binschedule']
        }

    },
})
