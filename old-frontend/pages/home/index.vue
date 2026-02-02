<template>
    <LayoutsDefault>

        <div class="flex w-full justify-end">
            <UButton label="Add Home" to="/home/create"/>
        </div>

        <UTable :columns="columns" :loading="isLoadingHomes" :rows="homes">
            <template #empty-state>
                <div class="flex flex-col items-center justify-center py-6 gap-3">
                    <span class="italic text-sm">No homes here!</span>
                    <UButton label="Add Home" to="/home/create"/>
                </div>
            </template>

            <template #name-data="{row}">
                <span>{{row.name}}</span>
                <UBadge v-if="row.active" class="ml-2">Main Home</UBadge>
            </template>

            <template #actions-data="{row}">
                <div class="flex flex-row space-x-2">
                    <UButton :to="'/home/' + row.id" color="gray">View</UButton>
                    <MakeHomeActive v-if="row.active === false" :home-id="row.id" @activated="loadHomes"></MakeHomeActive>
                    <DeleteHome :home-id="row.id" @deleted="loadHomes"></DeleteHome>
                </div>
            </template>
        </UTable>
    </LayoutsDefault>

</template>

<script lang="ts" setup>

definePageMeta({
    layout: 'home'
})

const columns = [
    {
        label: 'Name',
        key: 'name'
    },
    {
        label: 'Council',
        key: 'council'
    },
    {
        key: 'actions'
    }
]

const homes = ref<Home[]>([]);

const isLoadingHomes = ref<boolean>(true)

const loadHomes = () => {
    isLoadingHomes.value = true
    $fetch('/api/home')
        .then((response) => {
            homes.value = response.homes
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingHomes.value = false
        })
}

onMounted(() => {
    loadHomes();
})

</script>