<template>
    <UCard class="mt-10">
        <template #header>
            <div class="flex justify-between">
                <span class="flex flex-row items-center space-x-2">
                    <h1>When is bins?</h1>
                    <h2 class="text-sm">{{home?.name ?? ''}}</h2>
                </span>
                <div class="flex space-x-2 flex-row">
                    <UButton color="gray" label="Change Home" to="/home"/>
                    <ColorScheme>
                        <USelect v-model="$colorMode.preference" :options="['system', 'light', 'dark']"/>
                    </ColorScheme>
                </div>
            </div>
            <div class="flex justify-between">
                <UHorizontalNavigation :links="links" class="border-b border-gray-200 dark:border-gray-800"/>
            </div>
        </template>
        <slot/>
        <!--      <UButton icon="i-heroicons-book-open" to="https://ui.nuxt.com" target="_blank">Open Nuxt UI Documentation</UButton>-->
    </UCard>
</template>
<script lang="ts" setup>
const props = defineProps<{
    homeId: number
}>();

const home = ref<Home | null>(null)

onMounted(() => {
    loadHome();
})

const isLoadingHome = ref<boolean>(true)

const loadHome = () => {
    isLoadingHome.value = true
    $fetch(`/api/home/${props.homeId}`)
        .then((response) => {
            home.value = response.home || null
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingHome.value = false
        })
}

const links = [{
    label: 'Home Info',
    icon: 'i-heroicons-home',
    to: '/home/' + props.homeId
}, {
    label: 'Bins',
    icon: 'i-heroicons-trash',
    to: '/home/' + props.homeId + '/bins'
}, {
    label: 'Schedule',
    icon: 'i-heroicons-calendar',
    to: '/home/' + props.homeId + '/schedule'
}]
</script>