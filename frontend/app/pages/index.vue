<template>
  <div class="schedule-page">
    <UCard>
      <template #header>
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <h2 class="text-xl sm:text-2xl font-bold">Schedule & Calendar</h2>
          <div class="flex flex-col sm:flex-row gap-2 w-full sm:w-auto">
            <UButton icon="i-heroicons-arrow-path" @click="openAddScheduleModal" class="w-full sm:w-auto">
              <span class="hidden sm:inline">Add Schedule</span>
              <span class="sm:hidden">Schedule</span>
            </UButton>
            <UButton icon="i-heroicons-calendar-days" @click="openAddReplacementModal" class="w-full sm:w-auto">
              <span class="hidden sm:inline">Add Holiday Schedule</span>
              <span class="sm:hidden">Holiday</span>
            </UButton>
          </div>
        </div>
      </template>

      <div class="calendar-section">
        <!-- Bins Sidebar for Dragging -->
        <BinsSidebar :bins="bins" :is-loading="binsQuery.isLoading.value" />

        <!-- Calendar -->
        <div class="calendar-container">
          <div v-if="calendarQuery.isLoading.value">
            <USkeleton class="h-96 w-full" />
          </div>
          <FullCalendar
            v-else
            ref="calendarRef"
            :options="calendarOptions"
          />
        </div>
      </div>
    </UCard>

    <!-- Schedules Table -->
    <SchedulesTable :bins="bins" @edit="editSchedule" @delete="deleteScheduleConfirm" />

    <!-- Bin Day Replacements -->
    <BinDayReplacementsTable @delete="deleteReplacementConfirm" />

    <!-- Add/Edit Schedule Modal -->
    <ScheduleFormModal
      v-model:open="isScheduleModalOpen"
      :editing-schedule="editingSchedule"
      :bins="bins"
      :is-submitting="createSchedule.isPending.value || updateSchedule.isPending.value"
      :is-deleting="deleteSchedule.isPending.value"
      @submit="submitSchedule"
      @delete="handleDeleteFromModal"
      @cancel="isScheduleModalOpen = false"
    />

    <!-- Add Replacement Modal -->
    <ReplacementFormModal
      v-model:open="isReplacementModalOpen"
      :editing-replacement="editingReplacement"
      :is-submitting="createReplacement.isPending.value || updateReplacement.isPending.value"
      @submit="submitReplacement"
      @cancel="isReplacementModalOpen = false"
    />

    <!-- Event Drop Modal -->
    <EventDropModal
      v-model:open="isEventDropModalOpen"
      :event-data="eventDropData"
      :is-single-day-loading="createReplacement.isPending.value || updateReplacement.isPending.value || deleteReplacement.isPending.value"
      :is-schedule-loading="updateSchedule.isPending.value"
      @single-day-change="handleSingleDayChange"
      @schedule-change="handleScheduleChange"
      @cancel="isEventDropModalOpen = false"
    />

    <!-- Bin Status Modal -->
    <BinStatusModal
      v-model:open="isBinStatusModalOpen"
      :bin="selectedBin"
      :collection-date="selectedDate"
      :schedule="selectedSchedule"
      :replacement="selectedReplacement"
      :calendar-data="calendarQuery.data.value"
      @edit-schedule="editScheduleFromBinStatus"
      @edit-replacement="editReplacementFromBinStatus"
    />
  </div>
</template>

<script setup lang="ts">
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import type { CalendarOptions } from '@fullcalendar/core'
import { format, parseISO, startOfMonth, endOfMonth, addMonths } from 'date-fns'
import type { components } from '../../types/api'
import type { EventDropData } from '../components/EventDropModal.vue'
import type { BinCollection } from '../composables/useSchedulesQuery'

type Schedule = components['schemas']['Schedule']
type BinDayReplacement = components['schemas']['BinDayReplacement']
type Bin = components['schemas']['Bin']

const { binsQuery } = useBinsQuery()
const { schedulesQuery } = useSchedulesQuery()
const { replacementsQuery } = useBinDayReplacementsQuery()
const { createSchedule, updateSchedule, deleteSchedule } = useScheduleMutations()
const { createReplacement, updateReplacement, deleteReplacement } = useBinDayReplacementMutations()

const bins = computed(() => binsQuery.data.value?.items || [])
const schedules = computed(() => schedulesQuery.data.value?.items || [])
const replacements = computed(() => replacementsQuery.data.value?.items || [])

// Calendar setup
const calendarRef = ref()
const calendarStart = ref(startOfMonth(new Date()))
const calendarEnd = ref(endOfMonth(addMonths(new Date(), 2)))

const { calendarQuery } = useCalendarQuery(calendarStart, calendarEnd)

// Use calendar event handling composable
const { findScheduleForEvent, createEventDropData } = useCalendarEventHandling()

const calendarEvents = computed(() => {
  const collections = calendarQuery.data.value || []
  const events: any[] = []

  collections.forEach((collection) => {
    // Determine icon based on status
    let icon = ''
    switch (collection.status) {
      case 'taken_out':
        icon = '✓ ' // Check mark
        break
      case 'put_out_early':
        icon = '⚡ ' // Lightning bolt (indicates early action)
        break
      case 'collected':
        icon = '✅ ' // Check mark with box (completed)
        break
      case 'missed':
        icon = '✗ ' // X mark
        break
      case 'due_out':
        icon = '! ' // Exclamation mark
        break
      case 'not_yet_due':
        icon = '' // No icon
        break
    }

    events.push({
      title: icon + collection.bin_name,
      date: format(parseISO(collection.collection_due_at), 'yyyy-MM-dd'),
      backgroundColor: collection.bin_colour || '#888',
      borderColor: collection.bin_colour || '#888',
      extendedProps: {
        binId: collection.bin_id,
        status: collection.status,
      },
    })
  })

  return events
})

const calendarOptions = computed<CalendarOptions>(() => ({
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  events: calendarEvents.value,
  firstDay: 1, // 1 = Monday, 0 = Sunday

  editable: true,
  droppable: true,
  drop: handleBinDrop,
  eventDrop: handleEventDrop,
  eventClick: handleEventClick,
  datesSet: handleDatesSet,
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: '',
  },
}))

function handleDatesSet(dateInfo: any) {
  calendarStart.value = dateInfo.start
  calendarEnd.value = dateInfo.end
}

function handleBinDrop(dropInfo: any) {
  const binId = parseInt(dropInfo.draggedEl.dataset.binId || '0')
  const dropDate = dropInfo.dateStr

  openScheduleModalForDate(binId, dropDate)
}

// Bin status modal
const isBinStatusModalOpen = ref(false)
const selectedBin = ref<BinCollection | null>(null)
const selectedDate = ref<string | null>(null)
const selectedSchedule = ref<Schedule | null>(null)
const selectedReplacement = ref<BinDayReplacement | null>(null)

// Watch for calendar updates and refresh selectedBin when modal is open
watch(() => calendarQuery.data.value, (newCalendarData) => {
  // Only update if modal is open and we have a selected bin
  if (isBinStatusModalOpen.value && selectedBin.value && selectedDate.value && newCalendarData) {
    const updatedBin = newCalendarData.find(c =>
      c.bin_id === selectedBin.value?.bin_id &&
      format(parseISO(c.collection_due_at), 'yyyy-MM-dd') === selectedDate.value
    )

    if (updatedBin) {
      selectedBin.value = updatedBin
    }
  }
})

function handleEventClick(clickInfo: any) {
  const binId = clickInfo.event.extendedProps.binId
  const eventDate = format(clickInfo.event.start, 'yyyy-MM-dd')

  // Find the bin collection from calendar query
  const binCollection = calendarQuery.data.value?.find(c =>
    c.bin_id === binId &&
    format(parseISO(c.collection_due_at), 'yyyy-MM-dd') === eventDate
  )

  if (!binCollection) return

  // Check if there's a replacement that moves TO this date
  const replacement = replacements.value.find(
    (r: BinDayReplacement) => format(parseISO(r.replace_with as any), 'yyyy-MM-dd') === eventDate
  )

  // Find the schedule that generated this event
  const schedule = findScheduleForEvent(binId, eventDate)

  // Set modal data
  selectedBin.value = binCollection
  selectedDate.value = eventDate
  selectedSchedule.value = schedule
  selectedReplacement.value = replacement || null

  // Show bin status modal
  isBinStatusModalOpen.value = true
}

function editScheduleFromBinStatus(schedule: Schedule) {
  editSchedule(schedule)
}

function editReplacementFromBinStatus(replacement: BinDayReplacement) {
  editReplacement(replacement)
}

// Event drop handling (moving existing events)
const isEventDropModalOpen = ref(false)
const eventDropData = ref<EventDropData | null>(null)

function handleEventDrop(dropInfo: any) {
  // Prevent the event from moving immediately
  dropInfo.revert()

  const binId = dropInfo.event.extendedProps.binId
  const oldDate = format(dropInfo.oldEvent.start, 'yyyy-MM-dd')
  const newDate = format(dropInfo.event.start, 'yyyy-MM-dd')

  eventDropData.value = createEventDropData(binId, oldDate, newDate)
  isEventDropModalOpen.value = true
}

function handleSingleDayChange() {
  if (!eventDropData.value) return

  const { oldDate, newDate, originalDate, existingReplacementId } = eventDropData.value

  // If there's an existing replacement
  if (existingReplacementId) {
    // Check if we're moving back to the original date
    if (newDate === originalDate) {
      // Just delete the replacement
      deleteReplacement.mutate(existingReplacementId, {
        onSuccess: () => {
          isEventDropModalOpen.value = false
          eventDropData.value = null
        },
      })
    } else {
      // Delete the old replacement and create a new one
      // because we need to update both 'replace' and 'replace_with'
      deleteReplacement.mutate(existingReplacementId, {
        onSuccess: () => {
          createReplacement.mutate({
            replace: originalDate || oldDate,  // Use originalDate to maintain the link to the schedule
            replace_with: newDate,
          } as any, {
            onSuccess: () => {
              isEventDropModalOpen.value = false
              eventDropData.value = null
            },
          })
        },
      })
    }
  } else {
    // No existing replacement - create a new one
    createReplacement.mutate({
      replace: originalDate || oldDate,  // Use originalDate if available
      replace_with: newDate,
    } as any, {
      onSuccess: () => {
        isEventDropModalOpen.value = false
        eventDropData.value = null
      },
    })
  }
}

function handleScheduleChange() {
  if (!eventDropData.value || !eventDropData.value.scheduleId) return

  const { scheduleId, originalDate, newDate, existingReplacementId } = eventDropData.value
  const schedule = schedules.value.find((s: Schedule) => s.id === scheduleId)

  if (!schedule) return

  // Calculate the difference in days (use originalDate, not oldDate)
  const originalDateObj = parseISO(originalDate || newDate)
  const newDateObj = parseISO(newDate)
  const daysDiff = Math.floor((newDateObj.getTime() - originalDateObj.getTime()) / (1000 * 60 * 60 * 24))

  // Calculate the new start date
  const currentStart = parseISO(schedule.start)
  const newStart = new Date(currentStart)
  newStart.setDate(newStart.getDate() + daysDiff)

  // Update the schedule
  updateSchedule.mutate({
    id: scheduleId,
    data: {
      bin_id: schedule.bin_id,
      start: format(newStart, 'yyyy-MM-dd'),
      end: schedule.end ? format(parseISO(schedule.end), 'yyyy-MM-dd') : null,
      repeat_weeks: schedule.repeat_weeks,
    },
  }, {
    onSuccess: () => {
      // If there was an existing replacement, delete it since the schedule change makes it obsolete
      if (existingReplacementId) {
        deleteReplacement.mutate(existingReplacementId, {
          onSuccess: () => {
            isEventDropModalOpen.value = false
            eventDropData.value = null
          },
        })
      } else {
        isEventDropModalOpen.value = false
        eventDropData.value = null
      }
    },
  })
}

// Schedule form
const isScheduleModalOpen = ref(false)
const editingSchedule = ref<Schedule | null>(null)

function openAddScheduleModal() {
  editingSchedule.value = null
  isScheduleModalOpen.value = true
}

function openScheduleModalForDate(binId: number, date: string) {
  editingSchedule.value = null
  // We'll need to pass this info to the modal somehow
  // For now, open modal and let the component handle it
  isScheduleModalOpen.value = true
  // Set a temp schedule object with the bin and date
  nextTick(() => {
    editingSchedule.value = {
      bin_id: binId,
      start: date,
      end: null,
      repeat_weeks: 1,
    } as any
  })
}

function editSchedule(schedule: Schedule) {
  editingSchedule.value = schedule
  isScheduleModalOpen.value = true
}

function submitSchedule(formData: any) {
  if (!formData.bin_id) return

  const data = {
    bin_id: formData.bin_id,
    start: formData.start,
    end: formData.end || null,
    repeat_weeks: formData.repeat_weeks,
  }

  if (editingSchedule.value?.id) {
    updateSchedule.mutate({
      id: editingSchedule.value.id,
      data,
    }, {
      onSuccess: () => {
        isScheduleModalOpen.value = false
      },
    })
  } else {
    createSchedule.mutate(data as any, {
      onSuccess: () => {
        isScheduleModalOpen.value = false
      },
    })
  }
}

function deleteScheduleConfirm(schedule: Schedule) {
  if (confirm(`Delete this schedule for ${getBinById(schedule.bin_id)?.name}?`)) {
    deleteSchedule.mutate(schedule.id)
  }
}

function handleDeleteFromModal() {
  if (editingSchedule.value?.id) {
    deleteSchedule.mutate(editingSchedule.value.id, {
      onSuccess: () => {
        isScheduleModalOpen.value = false
      },
    })
  }
}

// Replacement form
const isReplacementModalOpen = ref(false)
const editingReplacement = ref<BinDayReplacement | null>(null)

function openAddReplacementModal() {
  editingReplacement.value = null
  isReplacementModalOpen.value = true
}

function editReplacement(replacement: BinDayReplacement) {
  editingReplacement.value = replacement
  isReplacementModalOpen.value = true
}

function submitReplacement(formData: any) {
  if (editingReplacement.value?.id) {
    updateReplacement.mutate({
      id: editingReplacement.value.id,
      data: formData as any,
    }, {
      onSuccess: () => {
        isReplacementModalOpen.value = false
      },
    })
  } else {
    createReplacement.mutate(formData as any, {
      onSuccess: () => {
        isReplacementModalOpen.value = false
      },
    })
  }
}

function deleteReplacementConfirm(replacement: BinDayReplacement) {
  if (confirm('Delete this bin day replacement?')) {
    deleteReplacement.mutate(replacement.id)
  }
}


// Helpers
function getBinById(id: number) {
  return bins.value.find((b: Bin) => b.id === id)
}
</script>

<style scoped>
.schedule-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 0.5rem;
}

@media (min-width: 640px) {
  .schedule-page {
    padding: 0 1rem;
  }
}

.calendar-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

@media (min-width: 768px) {
  .calendar-section {
    display: grid;
    grid-template-columns: 200px 1fr;
    gap: 1.5rem;
  }
}

.calendar-container {
  min-height: 400px;
  width: 100%;
}

@media (min-width: 768px) {
  .calendar-container {
    min-height: 600px;
  }
}

:deep(.fc) {
  font-family: inherit;
}

:deep(.fc-event) {
  cursor: pointer;
}

/* Make calendar responsive */
:deep(.fc .fc-toolbar) {
  flex-wrap: wrap;
  gap: 0.5rem;
}

:deep(.fc .fc-toolbar-title) {
  font-size: 1.25rem;
}

@media (min-width: 640px) {
  :deep(.fc .fc-toolbar-title) {
    font-size: 1.5rem;
  }
}
</style>

