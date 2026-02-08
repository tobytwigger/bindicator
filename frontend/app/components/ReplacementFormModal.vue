<template>
  <UModal v-model:open="isOpen" :title="editingReplacement ? 'Edit Bin Day Replacement' : 'Add Bin Day Replacement'">
    <template #body>
      <UForm :state="form" @submit="handleSubmit" class="space-y-4">
        <div class="space-y-2">
          <label class="block text-sm font-medium">
            Original Collection Date <span class="text-red-500">*</span>
          </label>
          <UInput
            v-model="form.replace"
            type="date"
            required
          />
        </div>

        <div class="space-y-2">
          <label class="block text-sm font-medium">
            New Collection Date <span class="text-red-500">*</span>
          </label>
          <UInput
            v-model="form.replace_with"
            type="date"
            required
          />
        </div>

        <div class="flex gap-2 justify-end">
          <UButton color="neutral" variant="ghost" @click="handleCancel">
            Cancel
          </UButton>
          <UButton type="submit" :loading="isSubmitting">
            {{ editingReplacement ? 'Update' : 'Create' }}
          </UButton>
        </div>
      </UForm>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import type { components } from '../../types/api'

type BinDayReplacement = components['schemas']['BinDayReplacement']

interface Props {
  open: boolean
  editingReplacement?: BinDayReplacement | null
  isSubmitting?: boolean
}

interface ReplacementFormData {
  replace: string
  replace_with: string
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  submit: [data: ReplacementFormData]
  cancel: []
}>()

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const form = ref<ReplacementFormData>({
  replace: '',
  replace_with: '',
})

// Watch for editing replacement changes to update form
watch(() => props.editingReplacement, (replacement) => {
  if (replacement) {
    form.value = {
      replace: replacement.replace as string,
      replace_with: replacement.replace_with as string,
    }
  } else {
    // Reset form when not editing
    form.value = {
      replace: '',
      replace_with: '',
    }
  }
}, { immediate: true })

function handleSubmit() {
  emit('submit', form.value)
}

function handleCancel() {
  emit('cancel')
  emit('update:open', false)
}
</script>
