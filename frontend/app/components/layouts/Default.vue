<template>
    <UCard class="mt-10">
        <template #header>
            <div class="flex justify-between items-center mb-4">
                <span class="flex flex-row items-center space-x-2">
                    <div class="text-xl font-bold">The Bindicator</div>
                </span>
                <div class="flex space-x-2 flex-row">
                    <ClientOnly>
                        <UButton
                            :icon="themeIcon"
                            color="neutral"
                            variant="ghost"
                            size="md"
                            @click="cycleTheme"
                            :aria-label="`Theme: ${colorMode.preference}`"
                        />
                    </ClientOnly>
                </div>
            </div>
            <div class="tabs-container">
                <UTabs :items="tabItems" v-model="activeTabIndex" :orientation="tabOrientation" class="tabs-full-width" />
            </div>
        </template>
        <slot/>
    </UCard>
</template>
<script lang="ts" setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const colorMode = useColorMode()

// Track window width for responsive tabs
const windowWidth = ref(1024)

const updateWindowWidth = () => {
    windowWidth.value = window.innerWidth
}

onMounted(() => {
    windowWidth.value = window.innerWidth
    window.addEventListener('resize', updateWindowWidth)
})

onUnmounted(() => {
    window.removeEventListener('resize', updateWindowWidth)
})

// Responsive tabs orientation
const tabOrientation = computed(() => {
    return windowWidth.value < 640 ? 'vertical' : 'horizontal'
})

// Theme icon based on current preference
const themeIcon = computed(() => {
    const preference = colorMode.preference
    if (preference === 'light') return 'i-heroicons-sun'
    if (preference === 'dark') return 'i-heroicons-moon'
    return 'i-heroicons-computer-desktop' // system
})

// Cycle through theme modes
function cycleTheme() {
    const modes = ['system', 'light', 'dark']
    const currentIndex = modes.indexOf(colorMode.preference)
    const nextIndex = (currentIndex + 1) % modes.length
    colorMode.preference = modes[nextIndex]
}

const tabItems = [
    {
        label: 'Bins',
        icon: 'i-heroicons-trash',
        to: '/',
        value: 0,
        click: () => router.push('/')
    },
    {
        label: 'Schedule',
        icon: 'i-heroicons-calendar',
        to: '/schedule',
        value: 1,
        click: () => router.push('/schedule')
    },
    {
        label: 'Settings',
        icon: 'i-heroicons-cog',
        to: '/settings',
        value: 2,
        click: () => router.push('/settings')
    }
]

// Track active tab value based on current route
const activeTabIndex = computed({
    get: () => {
        const currentPath = route.path

        // Normalize paths by removing trailing slashes for comparison
        const normalizePath = (path: string) => path.endsWith('/') && path.length > 1 ? path.slice(0, -1) : path
        const normalizedCurrentPath = normalizePath(currentPath)


        // Find exact match first
        let activeItem = tabItems.find(item => {
            const normalizedTo = normalizePath(item.to)
            return normalizedTo === normalizedCurrentPath
        })

        // If no exact match and not on root, try matching by checking if route starts with the tab's path
        if (!activeItem && currentPath !== '/') {
            activeItem = tabItems.find(item => {
                const normalizedTo = normalizePath(item.to)
                return normalizedTo !== '/' && normalizedCurrentPath.startsWith(normalizedTo)
            })
        }

        const result = activeItem ? activeItem.value : 0

        return result
    },
    set: (value) => {
        // When user clicks a tab, find the corresponding item and navigate
        const targetItem = tabItems.find(item => item.value === value)
        if (targetItem && targetItem.to !== route.path) {
            router.push(targetItem.to)
        }
    }
})
</script>

<style scoped>
.tabs-container {
    width: 100%;
}

.tabs-full-width {
    width: 100%;
}

.tabs-full-width :deep(.tabs) {
    width: 100%;
}

.tabs-full-width :deep([role="tablist"]) {
    width: 100%;
}

@media (max-width: 639px) {
    .tabs-container {
        margin-top: 0.5rem;
    }

    .tabs-full-width :deep([role="tablist"]) {
        display: flex;
        flex-direction: column;
        width: 100%;
    }

    .tabs-full-width :deep([role="tab"]) {
        width: 100%;
        justify-content: flex-start;
    }
}
</style>
