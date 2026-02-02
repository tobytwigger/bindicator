<template>
    <LayoutsHome :home-id="homeId">

        <div class="flex flex-row justify-end space-x-2">
            <NuxtLink :to="'/home/' + homeId + '/edit'">
                <UButton color="gray" icon="i-heroicons-pencil" label="Edit" />
            </NuxtLink>

            <UButton color="gray" @click="test" :loading="isTesting">Test</UButton>
        </div>

        <div class="mt-8 space-y-2">
            <div v-if="!hasBins">
                <NuxtLink :to="'/home/' + homeId + '/bins'">
                    <UAlert
                        icon="i-heroicons-trash"
                        color="orange"
                        variant="solid"
                        title="Set up bins"
                    />

                </NuxtLink>
            </div>

            <div v-if="!hasSchedule">
                <NuxtLink :to="'/home/' + homeId + '/schedule'">
                    <UAlert
                        icon="i-heroicons-trash"
                        color="orange"
                        variant="solid"
                        title="Set up schedule"
                        description="Tell the bindicator when your bins go out"
                    />
                </NuxtLink>
            </div>
        </div>

        <div class="flex flex-row space-x-4">
            <span class="font-bold">Home Name</span>
            <span>{{home?.name}}</span>
        </div>

        <div class="flex flex-col" v-if="selectedCouncil">

            <div class="flex flex-row space-x-4">
                <span class="font-bold">Council</span>
                <span>{{selectedCouncil?.name}}</span>
            </div>

            <div class="flex flex-col ml-4">
                <div class="flex flex-row space-x-4" v-for="key in Object.keys(home?.council_data ?? {})">
                    <span class="font-bold">{{ key }}</span>
                    <span>{{home?.council_data[key]}}</span>
                </div>
            </div>
        </div>

        <div class="flex flex-col space-y-2" v-if="home">
            <span class="font-bold">Settings</span>
            <div class="flex flex-row space-x-4 ml-8">
                <span class="font-bold">Timeout</span>
                <span>{{home.timeout ?? 'N/A' }}s</span>
            </div>
            <div class="flex flex-row space-x-4 ml-8">
                <span class="font-bold">When do you take your bins out?</span>
                <span>{{home.put_out_day_before ? 'The day before' : 'The day of' }}</span>
            </div>
        </div>

    </LayoutsHome>
</template>

<script lang="ts" setup>
import {Council} from "~/composables/useCouncils";

const route = useRoute();

const toast = useToast();

const {councils, councilSelectSchema, councilKeys} = useCouncils();

const selectedCouncil = computed<Council | null>(() => {
    return councils.find(council => council.key === home.value?.council) || null
})

const homeId = Number(route.params.id);

const home = ref<Home | null>(null)

onMounted(() => {
    loadHome();
})

const isLoadingHome = ref<boolean>(true)
const hasSchedule = ref<boolean>(false)
const hasBins = ref<boolean>(false)
const loadHome = () => {
    isLoadingHome.value = true
    $fetch(`/api/home/${homeId}`)
        .then((response) => {
            home.value = response.home || null
            hasSchedule.value = response.has_schedule
            hasBins.value = response.has_bins
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingHome.value = false
        })
}

const isTesting = ref<boolean>(false)

const test = () => {
    isTesting.value = true
    $fetch(`/api/home/${homeId}/test`)
        .then((response) => {
            if(response.valid) {
                toast.add({
                    title: 'Success',
                    description: 'Your connection is set up',
                })
            } else {
                toast.add({
                    title: 'Error',
                    description: 'There was an error setting up your connection',
                    color: 'red'
                })
            }
        })
        .catch((error) => {
            toast.add({
                title: 'Error',
                description: 'There was an error setting up your connection',
                color: 'red'
            })
        })
        .finally(() => {
            isTesting.value = false
        })
}

</script>