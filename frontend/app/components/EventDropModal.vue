<template>
  <UModal v-model:open="isOpen" title="Change Bin Collection">
    <template #body>
      <div v-if="eventData" class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          You've moved a bin collection from {{ formatDate(eventData.oldDate, 'MMM d, yyyy') }} to {{ formatDate(eventData.newDate, 'MMM d, yyyy') }}.
          <span v-if="eventData.existingReplacementId && eventData.newDate === eventData.originalDate">
            This will restore the bin to its original schedule date.
          </span>
          <span v-else-if="eventData.existingReplacementId">
            This date already has a replacement active.
          </span>
          <br>
          What would you like to do?
        </p>

        <div class="space-y-3">
          <UButton
            block
            size="lg"
            @click="handleSingleDayChange"
            :loading="isSingleDayLoading"
          >
            <div class="text-left">
              <div class="font-semibold">
                <span v-if="eventData.existingReplacementId && eventData.newDate === eventData.originalDate">
                  Remove the replacement
                </span>
                <span v-else-if="eventData.existingReplacementId">
                  Update the replacement
                </span>
                <span v-else>
                  Change this single day only
                </span>
              </div>
              <div class="text-xs opacity-75">
                <span v-if="eventData.existingReplacementId && eventData.newDate === eventData.originalDate">
                  Deletes the bin day replacement and returns to the normal schedule
                </span>
                <span v-else-if="eventData.existingReplacementId">
                  Updates the existing replacement to the new date
                </span>
                <span v-else>
                  For this week only, bins will be picked up on a different day
                </span>
              </div>
            </div>
          </UButton>

          <UButton
            v-if="eventData.scheduleId"
            block
            size="lg"
            color="primary"
            variant="outline"
            @click="handleScheduleChange"
            :loading="isScheduleLoading"
          >
            <div class="text-left">
              <div class="font-semibold">Change the entire schedule</div>
              <div class="text-xs opacity-75">
                This bin will always be picked up on this day
                <span v-if="eventData.existingReplacementId"> (and removes the replacement)</span>
              </div>
            </div>
          </UButton>

          <div v-else class="text-sm text-gray-500 italic p-3 bg-gray-50 dark:bg-gray-800 rounded">
            Unable to find a matching schedule for this event. You can only change this single day.
          </div>
        </div>

        <div class="flex justify-end pt-3">
          <UButton color="neutral" variant="ghost" @click="handleCancel">
            Cancel
          </UButton>
        </div>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { format, parseISO } from 'date-fns'

export interface EventDropData {
  binId: number
  oldDate: string
  newDate: string
  originalDate: string | null
  scheduleId: number | null
  existingReplacementId: number | null
}

interface Props {
  open: boolean
  eventData: EventDropData | null
  isSingleDayLoading?: boolean
  isScheduleLoading?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'single-day-change': []
  'schedule-change': []
  cancel: []
}>()

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

function formatDate(date: string | Date, formatStr: string) {
  try {
    const d = typeof date === 'string' ? parseISO(date) : date
    return format(d, formatStr)
  } catch {
    return 'Invalid date'
  }
}

function handleSingleDayChange() {
  emit('single-day-change')
}

function handleScheduleChange() {
  emit('schedule-change')
}

function handleCancel() {
  emit('cancel')
  emit('update:open', false)
}
</script>
