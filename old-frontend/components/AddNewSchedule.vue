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
    start: date().required('Required').min(new Date(), 'Start date must in the future'),
    end: date().min(new Date(), 'End date must in the future'),
    repeat_weeks: number().min(1).max(100).required('Required'),
    bins: array().of(
        string().required('Required')
    )
})

type Schema = InferType<typeof schema>

const state = reactive({
    start: undefined,
    end: null,
    repeat_weeks: undefined,
    bins: []
})

const isSubmitting = ref<boolean>(false);
const toast = useToast();
const onSubmit = (event: FormSubmitEvent<Schema>) => {
    isSubmitting.value = true;
    $fetch(`/api/home/${props.homeId}/schedule`, {
        method: 'POST',
        body: state
    })
        .then(res => {
            toast.add({
                title: 'Schedule created',
                description: 'The schedule has been created',
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

onMounted(() => {
    loadBins();
})

const bins = ref<Bin[]>([])
const isLoadingBins = ref<boolean>(true)
const loadBins = () => {
    isLoadingBins.value = true
    $fetch(`/api/home/${props.homeId}/bins`)
        .then((response) => {
            if(!Array.isArray(response.bins)) {
                bins.value = [response.bins]
            } else {
                bins.value = response.bins || [];
            }
        })
        .catch((error) => {
            console.error(error)
        })
        .finally(() => {
            isLoadingBins.value = false
        })
}

</script>

<template>
    <UForm :schema="schema" :state="state" class="space-y-4 m-4" @submit="onSubmit">
        <UFormGroup label="Start Date" name="start_date" hint="The first day these bins go out">
            <DatePickerPopup :is-required="true" v-model="state.start"></DatePickerPopup>
        </UFormGroup>

        <UFormGroup label="End Date" name="end_date" hint="When to end this schedule. Leave blank to run indefinitely.">
            <DatePickerPopup v-model="state.end"></DatePickerPopup>
        </UFormGroup>

        <UFormGroup label="Repeat every X weeks" name="repeat_weeks"
            hint="How often should this schedule repeat? E.g. every 2 weeks"
        >
            <UInput placeholder="2" v-model="state.repeat_weeks" type="number"></UInput>
        </UFormGroup>

        <UFormGroup label="Bins" name="bins" hint="Which bins go out on this schedule?">
            <USelectMenu v-model="state.bins" :options="bins"
                         value-attribute="id"
                         option-attribute="name"
                         multiple placeholder="Select bins">
                <template #empty>
                    <span v-if="isLoadingBins">
                        Loading bins...
                    </span>
                    <span v-else>
                        No bins found
                    </span>
                </template>
            </USelectMenu>
        </UFormGroup>

<!--        <UFormGroup label="Council" name="council">-->
<!--            <USelectMenu-->
<!--                v-model="state.council"-->
<!--                :options="councilSelectSchema"-->
<!--                class="w-full lg:w-48"-->
<!--                option-attribute="label"-->
<!--                placeholder="Select a council"-->
<!--                searchable-->
<!--                searchable-placeholder="Search councils..."-->
<!--                value-attribute="value"-->
<!--            />-->
<!--        </UFormGroup>-->

<!--        <div v-if="selectedCouncil">-->
<!--            <component :is="selectedCouncil.component"-->
<!--                       :key="selectedCouncil.key ?? 'unselected'"-->
<!--                       :properties="selectedCouncil.properties"-->
<!--                       :value="state.councilData"-->
<!--                       @update:value="state.councilData = $event">-->

<!--            </component>-->
<!--        </div>-->


        <UButton :loading="isSubmitting" type="submit" @click="onSubmit">
            Submit
        </UButton>
    </UForm>
</template>

<style scoped>

</style>