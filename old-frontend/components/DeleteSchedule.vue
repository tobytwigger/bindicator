<script setup lang="ts">
const props = defineProps<{
    homeId: number;
    scheduleId: number;
}>();

const toast = useToast();

const isOpen = ref(false);

const isDeleting = ref(false);

const emit = defineEmits<{
    (event: 'deleted')
}>();

const deleteSchedule = () => {
    isDeleting.value = true;
    $fetch(`/api/home/${props.homeId}/schedule/${props.scheduleId}`, {
        method: 'DELETE'
    })
        .then(() => {
            toast.add({
                title: 'Schedule deleted',
                description: 'The schedule has been deleted',
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
                Are you sure you want to delete this schedule?
            </div>
            <div class="flex justify-end p-4 gap-2">
                <UButton label="Cancel" :loading="isDeleting" @click="isOpen = false" />
                <UButton label="Delete" :loading="isDeleting" color="red" @click="deleteSchedule" />
            </div>
        </UModal>
    </div>

</template>

<style scoped>

</style>