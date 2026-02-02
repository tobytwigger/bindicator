<template>
    <LayoutsDefault>

        Create a home

        <home-form v-model="state" @submit="onSubmit">
            <template #submit="{onSubmit}">
                <UButton type="submit" :loading="isSubmitting">
                    Create Home
                </UButton>
            </template>
        </home-form>

    </LayoutsDefault>

</template>

<script lang="ts" setup>
import {object, string, type InferType} from 'yup'
import type {FormSubmitEvent} from '#ui/types'
import {Council} from "~/composables/useCouncils";
import type {HomeFormSchema} from "~/components/HomeForm.vue";

definePageMeta({
    layout: 'home'
})


const state = ref<HomeFormSchema>({
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
    $fetch('/api/home', {
        method: 'POST',
        body: state.value
    })
        .then(res => {
            toast.add({
                title: 'Home created',
                description: 'The home has been created',
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