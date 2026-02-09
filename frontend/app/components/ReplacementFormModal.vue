<template>
  <UModal v-model:open="isOpen" :title="editingReplacement ? 'Edit Bin Day Replacement' : 'Add Bin Day Replacement'">
    <template #body>
      <UForm :state="form" @submit="handleSubmit" class="space-y-4">
        <UFormField
          label="Original Collection Date"
          description="The scheduled collection date to replace"
          required
        >
          <UInputDate
            v-model="replaceDateValue"
            icon="i-heroicons-calendar"
          />
        </UFormField>

        <UFormField
          label="New Collection Date"
          description="The new date when bins will be collected instead"
          required
        >
          <UInputDate
            v-model="replaceWithDateValue"
            icon="i-heroicons-calendar"
          />
        </UFormField>

        <div class="flex gap-2 justify-end pt-2">
          <UButton color="neutral" variant="ghost" @click="handleCancel">
            Cancel
          </UButton>
          <UButton type="submit" :loading="isSubmitting" icon="i-heroicons-check">
            {{ editingReplacement ? 'Update' : 'Create' }}
          </UButton>
        </div>
      </UForm>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { CalendarDate, parseDate } from '@internationalized/date'
import type { components } from '~/types/api'

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

// Helper function to convert string date to CalendarDate object
function dateStringToCalendarDate(dateStr: string): CalendarDate | null {
  if (!dateStr) return null
  try {
    return parseDate(dateStr)
  } catch {
    return null
  }
}

// Helper function to convert CalendarDate object to string
function calendarDateToString(date: CalendarDate | null | undefined): string {
  if (!date) return ''
  return `${date.year}-${String(date.month).padStart(2, '0')}-${String(date.day).padStart(2, '0')}`
}

// Computed properties for UInputDate
const replaceDateValue = computed({
  get: () => dateStringToCalendarDate(form.value.replace),
  set: (value: CalendarDate | null | undefined) => {
    form.value.replace = calendarDateToString(value)
  }
})

const replaceWithDateValue = computed({
  get: () => dateStringToCalendarDate(form.value.replace_with),
  set: (value: CalendarDate | null | undefined) => {
    form.value.replace_with = calendarDateToString(value)
  }
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
