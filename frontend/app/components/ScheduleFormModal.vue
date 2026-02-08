<template>
  <UModal v-model:open="isOpen" :title="editingSchedule ? 'Edit Schedule' : 'Add Schedule'">
    <template #body>
      <UForm :state="form" @submit="handleSubmit" class="space-y-4">
        <div class="space-y-2">
          <label class="block text-sm font-medium">
            Bin <span class="text-red-500">*</span>
          </label>
          <USelect
            v-model="form.bin_id"
            :items="binOptions"
            placeholder="Select a bin"
          />
        </div>

        <div class="space-y-2">
          <label class="block text-sm font-medium">
            Start Date <span class="text-red-500">*</span>
          </label>
          <UInput
            v-model="form.start"
            type="date"
            required
          />
        </div>

        <div class="space-y-2">
          <label class="block text-sm font-medium">
            End Date (Optional)
          </label>
          <UInput
            v-model="form.end"
            type="date"
          />
        </div>

        <div class="space-y-2">
          <label class="block text-sm font-medium">
            Repeat Every (weeks) <span class="text-red-500">*</span>
          </label>
          <UInput
            v-model.number="form.repeat_weeks"
            type="number"
            min="1"
            required
          />
        </div>

        <div class="flex gap-2 justify-between">
          <UButton
            v-if="editingSchedule"
            color="red"
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
            <UButton type="submit" :loading="isSubmitting">
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
import type { components } from '../../types/api'

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
