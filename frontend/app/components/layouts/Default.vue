<template>
    <UCard class="mt-10">
        <template #header>
            <div class="flex justify-between">
                <span class="flex flex-row items-center space-x-2">
                    <div class="text-xl font-bold">The Bindicator</div>
                </span>
                <div class="flex space-x-2 flex-row">
                    <UButton color="neutral" label="Change Home" to="/home"/>
                    <ColorScheme>
                        <USelect v-model="$colorMode.preference" :options="['system', 'light', 'dark']"/>
                    </ColorScheme>
                </div>
            </div>
            <div class="flex justify-between">
                HELLO
                <UTabs :items="tabItems" v-model="activeTab" class="border-b border-gray-200 dark:border-gray-800" />
            </div>
        </template>
        <slot/>
        <!--      <UButton icon="i-heroicons-book-open" to="https://ui.nuxt.com" target="_blank">Open Nuxt UI Documentation</UButton>-->
    </UCard>
</template>
<script lang="ts" setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const links = [{
    label: 'Bins',
    icon: 'i-heroicons-trash',
    to: '/bins'
}, {
    label: 'Schedule',
    icon: 'i-heroicons-calendar',
    to: '/schedule'
}, {
    label: 'Settings',
    icon: 'i-heroicons-cog',
    to: '/settings'
}]

const tabItems = links.map(link => ({
    label: link.label,
    icon: link.icon
}))

const router = useRouter()
const route = useRoute()
const activeTab = ref(links.findIndex(link => link.to === route.path) !== -1 ? links.findIndex(link => link.to === route.path) : 0)

watch(() => route.path, (newPath) => {
    const idx = links.findIndex(link => link.to === newPath)
    if (idx !== -1) activeTab.value = idx
})

watch(activeTab, onTabChange)

function onTabChange(idx: number) {
    if (links[idx] == undefined || links[idx].to === route.path) {
        return
    }
    router.push(links[idx].to)
}
</script>