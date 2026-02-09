<template>
  <UModal v-model:open="isOpen" :title="editingSchedule ? 'Edit Schedule' : 'Add Schedule'">
    <template #body>
      <UForm :state="form" @submit="handleSubmit" class="space-y-4">
        <UFormField
          label="Bin"
          description="Select which bin to add to the schedule"
          required
        >
          <USelect
            v-model="form.bin_id"
            :items="binOptions"
            placeholder="Select a bin"
          />
        </UFormField>

        <UFormField
          label="Start Date"
          description="When this schedule begins"
          required
        >
          <UInputDate
            v-model="startDateValue"
            icon="i-heroicons-calendar"
          />
        </UFormField>

        <UFormField
          label="End Date"
          description="When this schedule ends (leave empty for ongoing)"
          hint="Optional"
        >
          <UInputDate
            v-model="endDateValue"
            icon="i-heroicons-calendar"
          />
        </UFormField>

        <UFormField
          label="Repeat Every"
          description="How many weeks between each collection"
          required
        >
          <div class="flex items-center gap-2">
            <UInput
              v-model.number="form.repeat_weeks"
              type="number"
              min="1"
              class="w-24"
            />
            <span class="text-sm text-gray-600 dark:text-gray-400">week{{ form.repeat_weeks !== 1 ? 's' : '' }}</span>
          </div>
        </UFormField>

        <div class="flex gap-2 justify-between">
          <UButton
            v-if="editingSchedule"
            color="error"
            variant="ghost"
            icon="i-heroicons-trash"
            @click="handleDelete"
            :loading="isDeleting"
          >
            Delete Schedule
          </UButton>
          <div v-else></div>
          <div class="flex gap-2">
            <UButton color="neutral" variant="ghost" @click="handleCancel">
              Cancel
            </UButton>
            <UButton type="submit" :loading="isSubmitting" icon="i-heroicons-check">
              {{ editingSchedule ? 'Update' : 'Create' }}
            </UButton>
          </div>
        </div>
      </UForm>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { format } from 'date-fns'
import { CalendarDate, parseDate } from '@internationalized/date'
import type { components } from '~/types/api'

type Schedule = components['schemas']['Schedule']
type Bin = components['schemas']['Bin']

interface Props {
  open: boolean
  editingSchedule?: Schedule | null
  bins: Bin[]
  isSubmitting?: boolean
  isDeleting?: boolean
}

interface ScheduleFormData {
  bin_id: number | null
  start: string
  end: string
  repeat_weeks: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  submit: [data: ScheduleFormData]
  cancel: []
  delete: []
}>()

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const form = ref<ScheduleFormData>({
  bin_id: null,
  start: '',
  end: '',
  repeat_weeks: 1,
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
const startDateValue = computed({
  get: () => dateStringToCalendarDate(form.value.start),
  set: (value: CalendarDate | null | undefined) => {
    form.value.start = calendarDateToString(value)
  }
})

const endDateValue = computed({
  get: () => dateStringToCalendarDate(form.value.end),
  set: (value: CalendarDate | null | undefined) => {
    form.value.end = calendarDateToString(value)
  }
})

const binOptions = computed(() =>
  props.bins.map((bin) => ({
    label: bin.name,
    value: bin.id,
  }))
)

// Watch for editing schedule changes to update form
watch(() => props.editingSchedule, (schedule) => {
  if (schedule) {
    form.value = {
      bin_id: schedule.bin_id,
      start: schedule.start,
      end: schedule.end || '',
      repeat_weeks: schedule.repeat_weeks,
    }
  } else {
    // Reset form when not editing
    form.value = {
      bin_id: null,
      start: format(new Date(), 'yyyy-MM-dd'),
      end: '',
      repeat_weeks: 1,
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

function handleDelete() {
  if (confirm('Are you sure you want to delete this schedule? This action cannot be undone.')) {
    emit('delete')
  }
}
</script>
