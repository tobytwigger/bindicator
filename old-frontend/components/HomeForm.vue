<script lang="ts" setup>
import {Council, type CouncilProperties} from "~/composables/useCouncils";
import {type InferType, object, string, number, boolean} from "yup";

const props = defineProps<{
    modelValue: HomeFormSchema
}>();

const {councils, councilSelectSchema, councilKeys} = useCouncils();

const selectedCouncil = computed<Council | null>(() => {
    return councils.find(council => council.key === props.modelValue?.council) || null
})

const schema = object({
    name: string().required('Required'),
    council: string().nullable().oneOf(councilKeys.value, 'Invalid council'),
    councilData: object().json(),
    timeout: number().min(1).max(21600),
    putOutDayBefore: boolean(),
})

export type HomeFormSchema = InferType<typeof schema>

const emit = defineEmits<{
    (event: 'submit'): void;
    (event: 'update:modelValue', value: HomeFormSchema): void;
}>();

const onSubmit = () => {
    console.log('submitting')
    emit('submit')
}

const state = computed<HomeFormSchema>({
    get() {
        return props.modelValue;
    },
    set(value: HomeFormSchema) {
        emit('update:modelValue', value);
    }
})

</script>

<template>

    <UForm :schema="schema" :state="state" class="space-y-4" @submit="onSubmit">
        <UFormGroup label="Name" name="name">
            <UInput v-model="state.name"/>
        </UFormGroup>

        <UDivider class="mt-8" label="Council Information"/>

        <div class="mt-8">

            <UFormGroup label="Council" name="council">
                <USelectMenu
                    v-model="state.council"
                    :options="councilSelectSchema"
                    class="w-full "
                    option-attribute="label"
                    placeholder="Other"
                    searchable
                    searchable-placeholder="Search councils..."
                    value-attribute="value"
                />
            </UFormGroup>

            <div v-if="selectedCouncil">
                <component :is="selectedCouncil.component"
                           :key="selectedCouncil.key ?? 'unselected'"
                           :properties="selectedCouncil.properties"
                           :value="state.councilData"
                           @update:value="state.councilData = $event">

                </component>
            </div>

        </div>



        <UDivider class="mt-8" label="Settings"/>

        <div class="mt-8">

            <UCard class="mt-4">
                <template #header>
                    These are settings for your bin-dicator. You can change them later.
                </template>

                <div class="space-y-8">
                    <UFormGroup label="Timeout" hint="The number of seconds before the screen turns off">
                        <UInput type="number" v-model="state.timeout" />
                    </UFormGroup>

                    <UFormGroup label="Put out day before" hint="Do you put your bins out the day before?">
                        <UToggle v-model="state.putOutDayBefore" size="lg"/>
                    </UFormGroup>
                </div>

            </UCard>

        </div>



        <slot name="submit" v-bind:submit="onSubmit">

        </slot>
    </UForm>

</template>

<style scoped>

</style>