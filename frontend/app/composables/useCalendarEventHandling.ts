import { parseISO } from 'date-fns'
import type { components } from '../../types/api'
import type { EventDropData } from '../components/EventDropModal.vue'

type Schedule = components['schemas']['Schedule']

/**
 * Find a schedule that could have generated an event on a specific date
 */
export function findScheduleForEvent(
  schedules: Schedule[],
  binId: number,
  dateStr: string
): Schedule | null {
  const date = parseISO(dateStr)

  for (const schedule of schedules) {
    if (schedule.bin_id !== binId) continue

    const scheduleStart = parseISO(schedule.start)
    const scheduleEnd = schedule.end ? parseISO(schedule.end) : null

    // Check if date is within schedule range
    if (date < scheduleStart) continue
    if (scheduleEnd && date > scheduleEnd) continue

    // Check if date matches the schedule pattern
    const daysSinceStart = Math.floor((date.getTime() - scheduleStart.getTime()) / (1000 * 60 * 60 * 24))
    const weeksSinceStart = daysSinceStart / 7

    if (weeksSinceStart % schedule.repeat_weeks === 0) {
      return schedule
    }
  }

  return null
}

/**
 * Composable for handling calendar event interactions
 */
export function useCalendarEventHandling() {
  const { schedulesQuery } = useSchedulesQuery()
  const { replacementsQuery } = useBinDayReplacementsQuery()

  const schedules = computed(() => schedulesQuery.data.value?.items || [])
  const replacements = computed(() => replacementsQuery.data.value?.items || [])

  /**
   * Create event drop data from a FullCalendar drop event
   */
  function createEventDropData(
    binId: number,
    oldDate: string,
    newDate: string
  ): EventDropData {
    // Check if there's an existing replacement for this date
    console.log('createEventDropData - Looking for replacement with replace_with =', oldDate)
    console.log('createEventDropData - Available replacements:', replacements.value)

    const existingReplacement = replacements.value.find(
      (r: any) => {
        const replaceWith = typeof r.replace_with === 'string'
          ? r.replace_with.split('T')[0]  // Always extract just the date part
          : r.replace_with?.toISOString?.()?.split('T')[0]
        console.log('  Checking replacement:', r.id, 'replace_with:', replaceWith, 'matches:', replaceWith === oldDate)
        return replaceWith === oldDate
      }
    )

    console.log('createEventDropData - Found existing replacement:', existingReplacement)

    // If there's a replacement, the original date is the 'replace' date
    // Otherwise, the original date is the oldDate itself
    const originalDate = existingReplacement
      ? (typeof existingReplacement.replace === 'string'
          ? existingReplacement.replace.split('T')[0]  // Always extract just the date part
          : existingReplacement.replace?.toISOString?.()?.split('T')[0])
      : oldDate

    // Find the schedule that could have generated this event (use original date)
    const matchingSchedule = findScheduleForEvent(schedules.value, binId, originalDate || oldDate)

    return {
      binId,
      oldDate,
      newDate,
      originalDate: originalDate || null,
      scheduleId: matchingSchedule?.id || null,
      existingReplacementId: existingReplacement?.id || null,
    }
  }

  return {
    findScheduleForEvent: (binId: number, dateStr: string) =>
      findScheduleForEvent(schedules.value, binId, dateStr),
    createEventDropData,
    schedules,
    replacements,
  }
}
