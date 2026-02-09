<template>
  <UModal v-model:open="isOpen" title="Bin Status">
    <template #body>
      <div v-if="bin && collectionDate" class="space-y-4">
        <!-- Bin Info -->
        <div class="flex items-center gap-3">
          <div
            class="w-8 h-8 rounded-full"
            :style="{ backgroundColor: bin.colour || '#888' }"
          ></div>
          <div>
            <h3 class="font-semibold text-lg">{{ bin.name }}</h3>
            <p class="text-sm text-gray-500">{{ formatDate(collectionDate, 'EEEE, MMMM d, yyyy') }}</p>
          </div>
        </div>

        <!-- Status Display -->
        <div class="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-2xl">{{ statusIcon }}</span>
              <div>
                <p class="font-medium">{{ statusText }}</p>
                <p v-if="bin.put_out_date" class="text-sm text-gray-500">
                  Put out on {{ formatDate(bin.put_out_date, 'MMM d, yyyy') }}
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Actions -->
        <div class="space-y-2">
          <div v-if="bin.status === 'taken_out' || bin.status === 'put_out_early' || bin.status === 'due_out' || bin.status === 'not_yet_due'" class="space-y-2">
            <p class="text-sm text-gray-600 dark:text-gray-400">
              <span v-if="bin.status === 'due_out' && canPutOut">Mark this bin as:</span>
              <span v-else-if="bin.status === 'not_yet_due' && canPutOut">This bin is not yet due, but you can mark it as put out early:</span>
              <span v-else-if="bin.status === 'not_yet_due' && !canPutOut">This bin is not yet due:</span>
              <span v-else-if="bin.status === 'put_out_early'">This bin was put out early:</span>
              <span v-else-if="bin.status === 'taken_out'">This bin has been marked as put out:</span>
              <span v-else-if="bin.status === 'due_out' && !canPutOut">This bin is due, but has an earlier collection pending:</span>
            </p>
            <div class="flex flex-col sm:flex-row gap-2">
              <UButton
                v-if="canPutOut"
                @click="markAsPutOut"
                :loading="createBinPutOut.isPending.value"
                color="success"
                icon="i-heroicons-check-circle"
                class="flex-1"
              >
                {{ bin.status === 'not_yet_due' ? 'Put Out Early' : 'Put Out' }}
              </UButton>
              <UButton
                v-if="(bin.status === 'taken_out' || bin.status === 'put_out_early') && putOutRecordId"
                @click="confirmUndo"
                :loading="deleteBinPutOut.isPending.value"
                color="warning"
                variant="outline"
                icon="i-heroicons-arrow-uturn-left"
                class="flex-1"
              >
                Undo Put Out
              </UButton>
            </div>
            <p v-if="bin.status === 'taken_out' || bin.status === 'put_out_early'" class="text-xs text-gray-500 dark:text-gray-400">
              Click "Undo Put Out" if you marked this bin by mistake or brought it back inside.
            </p>
            <p v-if="bin.status === 'not_yet_due' && canPutOut" class="text-xs text-blue-600 dark:text-blue-400">
              💡 Tip: Use this when you're going away and need to put the bin out early.
            </p>
            <p v-if="hasEarlierUncollectedBin" class="text-xs text-orange-600 dark:text-orange-400">
              ⚠️ An earlier collection for this bin is still pending. Put that one out first.
            </p>
          </div>

          <div v-else-if="bin.status === 'missed'" class="space-y-2">
            <div class="bg-red-50 dark:bg-red-900/20 p-3 rounded-lg">
              <p class="text-sm text-red-700 dark:text-red-300">
                This bin was not put out and the collection time has passed.
              </p>
            </div>
            <!-- Allow marking as put out even if missed, in case user wants to track it -->
            <UButton
              @click="markAsPutOut"
              :loading="createBinPutOut.isPending.value"
              color="success"
              icon="i-heroicons-check-circle"
              variant="outline"
              class="w-full"
              size="sm"
            >
              Mark as Put Out Anyway
            </UButton>
          </div>
        </div>

        <!-- Existing Actions (Edit Schedule/Replacement) -->
        <div class="border-t pt-4">
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-2">
            Schedule Actions:
          </p>
          <div class="flex gap-2">
            <UButton
              v-if="schedule"
              @click="onEditSchedule"
              color="neutral"
              variant="outline"
              icon="i-heroicons-calendar"
              class="flex-1"
            >
              Edit Schedule
            </UButton>
            <UButton
              v-if="replacement"
              @click="onEditReplacement"
              color="neutral"
              variant="outline"
              icon="i-heroicons-calendar-days"
              class="flex-1"
            >
              Edit Holiday
            </UButton>
          </div>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex justify-end">
        <UButton color="neutral" variant="ghost" @click="handleClose">
          Close
        </UButton>
      </div>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { format as formatDate } from 'date-fns'
import type { CalendarBin, CalendarDate } from '../composables/useSchedulesQuery'
import type { components } from '../../types/api'

type Schedule = components['schemas']['Schedule']
type BinDayReplacement = components['schemas']['BinDayReplacement']

interface Props {
  open: boolean
  bin?: CalendarBin | null
  collectionDate?: string | null
  schedule?: Schedule | null
  replacement?: BinDayReplacement | null
  calendarData?: CalendarDate[] | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:open': [value: boolean]
  'edit-schedule': [schedule: Schedule]
  'edit-replacement': [replacement: BinDayReplacement]
}>()

const isOpen = computed({
  get: () => props.open,
  set: (value) => emit('update:open', value)
})

const { createBinPutOut, deleteBinPutOut } = useBinPutOutMutations()

const putOutRecordId = computed(() => {
  // Simply return the put_out_id from the bin prop
  return props.bin?.put_out_id || null
})

// Check if there are earlier collections for the same bin that haven't been collected yet
const hasEarlierUncollectedBin = computed(() => {
  if (!props.bin || !props.collectionDate || !props.calendarData) return false

  const currentDate = props.collectionDate

  // Find all earlier calendar entries for the same bin
  for (const dateEntry of props.calendarData) {
    // Skip if this is the current date or later
    if (dateEntry.date >= currentDate) continue

    // Check if this date has the same bin
    const sameBin = dateEntry.bins.find(b => b.id === props.bin?.id)
    if (!sameBin) continue

    // Check if the bin hasn't been collected yet
    // 'collected' and 'missed' statuses mean the collection event has passed
    // These statuses indicate the bin collection is still pending:
    if (sameBin.status === 'not_yet_due' || sameBin.status === 'due_out' ||
        sameBin.status === 'taken_out' || sameBin.status === 'put_out_early') {
      return true
    }
  }

  return false
})

// Determine if we should show the "Put Out" button
const canPutOut = computed(() => {
  if (!props.bin) return false

  // If there's an earlier uncollected bin, don't allow putting out this one
  if (hasEarlierUncollectedBin.value) return false

  // Otherwise, allow if status is 'due_out' or 'not_yet_due'
  return props.bin.status === 'due_out' || props.bin.status === 'not_yet_due'
})

const statusIcon = computed(() => {
  if (!props.bin) return ''
  switch (props.bin.status) {
    case 'taken_out': return '✓'
    case 'put_out_early': return '⚡'
    case 'collected': return '✅'
    case 'missed': return '✗'
    case 'due_out': return '!'
    case 'not_yet_due': return '⏰'
    default: return ''
  }
})

const statusText = computed(() => {
  if (!props.bin) return ''
  switch (props.bin.status) {
    case 'taken_out': return 'Bin Put Out'
    case 'put_out_early': return 'Bin Put Out Early'
    case 'collected': return 'Collected'
    case 'missed': return 'Missed Collection'
    case 'due_out': return 'Due to be Put Out'
    case 'not_yet_due': return 'Not Yet Due'
    default: return ''
  }
})

function markAsPutOut() {
  if (!props.bin || !props.collectionDate) return

  // Create a put out record with the current datetime
  createBinPutOut.mutate({
    bin_id: props.bin.id,
    date_put_out_at: new Date().toISOString(),
  }, {
    onSuccess: () => {
      // Modal will update automatically via query invalidation
    }
  })
}

function confirmUndo() {
  // Ask for confirmation before undoing
  if (confirm('Are you sure you want to undo marking this bin as put out? This will remove the record that the bin was taken outside.')) {
    markAsNotPutOut()
  }
}

function markAsNotPutOut() {
  if (!putOutRecordId.value) return

  deleteBinPutOut.mutate(putOutRecordId.value, {
    onSuccess: () => {
      // Modal will update automatically via query invalidation
    }
  })
}

function onEditSchedule() {
  if (props.schedule) {
    emit('edit-schedule', props.schedule)
    handleClose()
  }
}

function onEditReplacement() {
  if (props.replacement) {
    emit('edit-replacement', props.replacement)
    handleClose()
  }
}

function handleClose() {
  emit('update:open', false)
}
</script>
