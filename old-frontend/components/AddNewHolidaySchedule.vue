<script lang="ts" setup>

import {type InferType, object, string, date, array, number} from "yup";
import type {FormSubmitEvent} from "#ui/types";
import type {Bin} from "~/server/utils/drizzle";

const props = defineProps<{
    homeId: number
}>();

const emit = defineEmits<{
    (event: 'updated'): void
}>();

const schema = object({
    replace: date().required('Required'),
    with: date(),
})

type Schema = InferType<typeof schema>

const state = reactive({
    replace: null,
    with: null,
})

const isSubmitting = ref<boolean>(false);
const toast = useToast();
const onSubmit = (event: FormSubmitEvent<Schema>) => {
    isSubmitting.value = true;
    $fetch(`/api/home/${props.homeId}/bin-day-replacement`, {
        method: 'POST',
        body: state
    })
        .then(res => {
            toast.add({
                title: 'Holiday schedule added',
                description: 'The holiday schedule has been added',
            })
            emit('updated');
        })
        .catch(err => {
            console.error(err)
        })
        .finally(() => {
            isSubmitting.value = false;
        })
}

</script>

<template>
    <div>

        <UForm :schema="schema" :state="state" class="space-y-4 m-4" @submit="onSubmit">
            <UFormGroup label="If your bins are usually" name="replace" hint="Your normal bin day">
                <DatePickerPopup :is-required="true" v-model="state.replace"></DatePickerPopup>
            </UFormGroup>

            <UFormGroup label="Then pick up will be on" name="with" hint="When these bins will be picked up unstead">
                <DatePickerPopup :is-required="true" v-model="state.with"></DatePickerPopup>
            </UFormGroup>

            <UButton :loading="isSubmitting" type="submit" @click="onSubmit">
                Submit
            </UButton>
        </UForm>
    </div>
</template>

<style scoped>

</style>