<script setup lang="ts">
const props = defineProps<{
    homeId: number;
    replacementBinDayId: number;
}>();

const toast = useToast();

const isOpen = ref(false);

const isDeleting = ref(false);

const emit = defineEmits<{
    (event: 'deleted')
}>();

const deleteReplacementBinDay = () => {
    isDeleting.value = true;
    $fetch(`/api/home/${props.homeId}/bin-day-replacement/${props.replacementBinDayId}`, {
        method: 'DELETE'
    })
        .then(() => {
            toast.add({
                title: 'Holiday schedule deleted',
                description: 'The holiday schedule has been deleted',
            })
            emit('deleted');
        })
        .catch((error) => {
            console.error(error);
        })
        .finally(() => {
            isDeleting.value = false;
            isOpen.value = false;
        });
}

</script>

<template>

    <div>
        <UButton
            icon="i-heroicons-trash"
            color="red"
            label="Delete"
            @click="isOpen = true" />

        <UModal v-model="isOpen">
            <div class="p-4">
                Are you sure you want to delete this holiday schedule?
            </div>
            <div class="flex justify-end p-4 gap-2">
                <UButton label="Cancel" :loading="isDeleting" @click="isOpen = false" />
                <UButton label="Delete" :loading="isDeleting" color="red" @click="deleteReplacementBinDay" />
            </div>
        </UModal>
    </div>

</template>

<style scoped>

</style>