<script lang="ts" setup>
import type {Bin} from "~/server/utils/drizzle";
import {object, string, type InferType} from 'yup'
import type {FormSubmitEvent} from "#ui/types";
import * as wasi from "node:wasi";

const props = defineProps<{
    position: number,
    options: string[],
    bin: Bin | null,
    homeId: number
}>();

const toast = useToast();

const emit = defineEmits<{
    (event: 'updated'): void
}>();


const schema = object({
    humanName: string().required('Required'),
    option: string().oneOf(props.options, 'Invalid option').required('Required')
})

type Schema = InferType<typeof schema>

const state = ref<Schema>({
    humanName: '',
    option: '',
})

const isSubmitting = ref(false);
const wasUpdated = ref<boolean>(true); // Initially true, so that when the bins load for the first time we update

const updateBin = () => {
    isSubmitting.value = true;
    $fetch(`/api/home/${props.homeId}/bins/${props.position}`, {
        method: 'POST',
        body: state.value
    })
        .then(() => {
            wasUpdated.value = true;
            toast.add({
                title: 'Bin updated',
                description: 'The bin has been updated',
            })
            emit('updated');
        })
        .catch((error) => {
            console.error(error);
        })
        .finally(() => {
            isSubmitting.value = false;
        });
}

const isDirty = computed(() => {
    return state.value.humanName !== (props.bin?.name ?? '') || state.value.option !== (props.bin?.council_name ?? '')
})

watch(() => props.bin, () => {
    if(wasUpdated.value) {
        wasUpdated.value = false;
        state.value.humanName = props.bin?.name ?? ''
        state.value.option = props.bin?.council_name ?? ''
    }
})

onMounted(() => {
    state.value.humanName = props.bin?.name ?? ''
    state.value.option = props.bin?.council_name ?? ''
})

const isDeleting = ref(false);

const del = () => {
    isDeleting.value = true;
    $fetch(`/api/home/${props.homeId}/bins/${props.position}`, {
        method: 'DELETE'
    })
        .then(() => {
            wasUpdated.value = true;
            toast.add({
                title: 'Bin cleared',
                description: 'The bin has been cleared',
            })
            emit('updated')
        })
        .catch((error) => {
            console.error(error);
        })
        .finally(() => {
            isDeleting.value = false;
        });
}

const isMoving = ref(false);
const moveForwards = () => {
    move('forwards');
}

const moveBack = () => {
    move('backwards');
}

const move = (direction) => {
    isMoving.value = true;
    $fetch(`/api/home/${props.homeId}/bins/${props.position}/move`, {
        method: 'POST',
        body: {
            direction
        }
    })
        .then(() => {
            toast.add({
                title: 'Bin moved',
                description: 'The bin has been moved',
            })
            emit('updated');
        })
        .catch((error) => {
            console.error(error);
        })
        .finally(() => {
            isMoving.value = false;
            emit('updated')
        });
}

</script>

<template>
    <div class="text-center flex flex-col p-2">
    <span>
        Bin {{ position }}
    </span>

        <span>
        <UForm :schema="schema" :state="state" class="space-y-4" @submit="updateBin">
            <UFormGroup label="Name" name="name">
                <UInput v-model="state.humanName"/>
            </UFormGroup>

            <UFormGroup label="Bin" name="bin"
                        v-if="props.options.length > 0"
            >
                <USelectMenu
                    v-if="props.options.length > 0"
                    v-model="state.option"
                    :options="props.options"
                    class="w-full"
                    placeholder="Select a bin from the council"
                    searchable
                    searchable-placeholder="Search bins..."
                />
            </UFormGroup>

            <div class="flex flex-row m-2 justify-between w-full">
                <div>
                     <UButton icon="i-heroicons-chevron-left" color="gray" :loading="isMoving" @click="moveBack" v-if="props.position !== 1"
                              class="w-min">
                    </UButton>
                </div>
                <div class="flex flex-col space-y-2 w-full text-center m-auto justify-center items-center">
                <UButton icon="i-material-symbols-save-outline" class="w-min"
                         v-if="isDirty" :loading="isSubmitting" type="submit"
                         @click="updateBin">
                    Save
                </UButton>
                    <UButton icon="i-heroicons-trash" class="w-min"
                         v-if="props.bin !== null" :loading="isDeleting" color="red"
                         @click="del">
                    Clear
                </UButton>
            </div>

                <div>
                 <UButton icon="i-heroicons-chevron-right" color="gray" :loading="isMoving" @click="moveForwards" v-if="props.position !== 4"
                          class="w-min">
                </UButton>
                </div>
            </div>


        </UForm>
    </span>
    </div>
</template>

<style scoped>

</style>