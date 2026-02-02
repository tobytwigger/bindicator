<script setup lang="ts">
import {date} from "yup";

import { format } from 'date-fns'

const props = defineProps({
    modelValue: {
        type: [Date, Object] as PropType<DatePickerDate | DatePickerRangeObject | null>,
        default: null
    },
    isRequired: {
        type: Boolean,
        default: false
    }
})

const emit = defineEmits(['update:model-value'])

const date = computed({
    get: () => props.modelValue,
    set: (value) => {
        emit('update:model-value', value)
    }
})

const buttonLabel = computed<string|null>(() => {
    if(date.value) {
        return format(date.value, 'd MMM, yyy')
    }

    if(props.isRequired) {
        return 'Please select';
    }

    return 'Select a date';
})

</script>

<template>
    <UPopover :popper="{ placement: 'bottom-start' }">
        <UButton color="gray" icon="i-heroicons-calendar-days-20-solid" :label="buttonLabel" />

        <template #panel="{ close }">
            <DatePicker v-model="date" :is-required="props.isRequired" @close="close" />
        </template>
    </UPopover>
</template>
