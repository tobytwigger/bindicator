<script setup lang="ts">
import {type CouncilProperties} from "~/composables/useCouncils";

interface Def {
    house_number: null|string
    postcode: null|string
}
const props = withDefaults(defineProps<{
    properties?: CouncilProperties[]
    value: {
        house_number?: null|string
        postcode?: null|string
        uprn?: null|string
    }
}>(), {
    properties: () => [],
    value: () => {}
});

onMounted(() => {
    let d = {}
    if(props.properties) {
        props.properties.forEach(p => {
            d[p] = props.value[p] || null;
        })
    }
    dynamicModel.value = d;
})

const emit = defineEmits<{
    (event: 'update:value', value: object): void
}>();

const dynamicModel = computed<Def>({
    get() {
        return props.value;
    },
    set(value: object) {
        emit('update:value', value);
    }
});

</script>

<template>

    <UCard class="mt-4">
        <template #header>
            To use the council information, we need to know more about your property.

            You may leave this blank and fill it in later.
        </template>

        <div>
            <UFormGroup label="House number" v-if="props.properties.includes(CouncilProperties.HouseNumber)">
                <UInput v-model="dynamicModel.house_number" />
            </UFormGroup>

            <UFormGroup label="Postcode" v-if="props.properties.includes(CouncilProperties.Postcode)">
                <UInput v-model="dynamicModel.postcode" />
            </UFormGroup>

            <UFormGroup label="UPRN" hint="Find your house UPRN at https://www.findmyaddress.co.uk/search" v-if="props.properties.includes(CouncilProperties.Uprn)">
                <UInput v-model="dynamicModel.uprn" />
            </UFormGroup>
        </div>

    </UCard>

</template>

<style scoped>

</style>