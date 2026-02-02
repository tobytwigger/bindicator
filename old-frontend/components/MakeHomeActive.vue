<script setup lang="ts">
const props = defineProps<{
    homeId: number;
}>();

const toast = useToast();

const isOpen = ref(false);

const isMakingActive = ref(false);

const emit = defineEmits<{
    (event: 'activated')
}>();

const makeHomeActive = () => {
    isMakingActive.value = true;
    $fetch(`/api/home/${props.homeId}/activate`, {
        method: 'POST'
    })
        .then(() => {
            toast.add({
                title: 'Home activated',
                description: 'The home has been activated',
            })
            emit('activated');
        })
        .catch((error) => {
            console.error(error);
        })
        .finally(() => {
            isMakingActive.value = false;
            isOpen.value = false;
        });
}

</script>

<template>

    <div>
        <UButton
            icon="i-heroicons-light-bulb"
            color="gray"
            label="Activate"
            @click="isOpen = true" />

        <UModal v-model="isOpen">
            <div class="p-4">
                Are you sure you want to use this home on the bindicator?
            </div>
            <div class="flex justify-end p-4 gap-2">
                <UButton label="Cancel" color="gray" :loading="isMakingActive" @click="isOpen = false" />
                <UButton label="Make Active" :loading="isMakingActive" color="primary" @click="makeHomeActive" />
            </div>
        </UModal>
    </div>

</template>

<style scoped>

</style>