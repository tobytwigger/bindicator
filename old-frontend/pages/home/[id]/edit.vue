<template>
    <LayoutsDefault>

        Update Home

        <UProgress v-if="isLoadingHome" animation="carousel" />

        <home-form v-model="state" @submit="onSubmit">
            <template #submit="{onSubmit}">
                <UButton type="submit" :loading="isSubmitting">
                    Update Home
                </UButton>
            </template>
        </home-form>
    </LayoutsDefault>

</template>

<script lang="ts" setup>
import {object, string, type InferType} from 'yup'
import type {FormSubmitEvent} from '#ui/types'
import {Council} from "~/composables/useCouncils";

const {councils, councilSelectSchema, councilKeys} = useCouncils();

const route = useRoute();

const homeId = Number(route.params.id);

const home = ref<Home | null>(null)

onMounted(() => {
    loadHome();
})

const isLoadingHome = ref<boolean>(true)
const loadHome = () => {
    isLoadingHome.value = true
    $fetch(`/api/home/${homeId}`)
        .then((response) => {
            home.value = response.home || null
            state.value.name = response.home?.name || null
            state.value.council = response.home?.council || null
            state.value.councilData = response.home?.council_data || {}
            state.value.timeout = response.home?.timeout || 60
            state.value.putOutDayBefore = response.home?.put_out_day_before || false
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingHome.value = false
        })
}



const state = ref({
    name: undefined,
    council: undefined,
    councilData: {},
    timeout: 60,
    putOutDayBefore: false,
})

const isSubmitting = ref<boolean>(false);
const toast = useToast();
const onSubmit = () => {
    isSubmitting.value = true;
    $fetch('/api/home/' + homeId, {
        method: 'POST',
        body: state.value
    })
        .then(res => {
            toast.add({
                title: 'Home updated',
                description: 'The home has been updated',
            })
            navigateTo('/home/' + res.id)
        })
        .catch(err => {
            console.error(err)
        })
        .finally(() => {
            isSubmitting.value = false;
        })
}

</script>