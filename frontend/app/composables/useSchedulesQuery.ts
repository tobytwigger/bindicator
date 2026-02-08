import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import type { components } from '~/types/api'
import { format } from 'date-fns'

type Schedule = components['schemas']['Schedule']
type ScheduleCreate = components['schemas']['ScheduleCreate']
type ScheduleEdit = components['schemas']['ScheduleEdit']
type PaginationResponse = components['schemas']['PaginationResponse_Schedule_']

export interface CalendarBin {
  id: number
  name: string
  colour: string
}

export interface CalendarDate {
  date: string
  bins: CalendarBin[]
}

export function useSchedulesQuery(page = ref(1), perPage = ref(100)) {
  const { apiFetch } = useApi()

  const schedulesQuery = useQuery({
    queryKey: ['schedules', page, perPage],
    queryFn: () => apiFetch<PaginationResponse>(`/schedules/?page=${page.value}&per_page=${perPage.value}`),
  })

  return { schedulesQuery }
}

export function useCalendarQuery(start: Ref<Date>, end: Ref<Date>) {
  const { apiFetch } = useApi()

  const calendarQuery = useQuery({
    queryKey: ['calendar', start, end],
    queryFn: () => {
      const startStr = format(start.value, 'yyyy-MM-dd')
      const endStr = format(end.value, 'yyyy-MM-dd')
      return apiFetch<CalendarDate[]>(`/schedules/calendar?start=${startStr}&end=${endStr}`)
    },
    enabled: computed(() => !!start.value && !!end.value),
  })

  return { calendarQuery }
}

export function useScheduleMutations() {
  const { apiFetch } = useApi()
  const queryClient = useQueryClient()
  const toast = useToast()

  const createSchedule = useMutation({
    mutationFn: (schedule: ScheduleCreate) => {
      // Convert dates to ISO date strings (YYYY-MM-DD)
      const payload = {
        ...schedule,
        start: format(new Date(schedule.start), 'yyyy-MM-dd'),
        end: schedule.end ? format(new Date(schedule.end), 'yyyy-MM-dd') : null,
      }
      return apiFetch<Schedule>('/schedules/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.add({ title: 'Schedule created successfully', color: 'green' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to create schedule',
        description: error.detail || 'An error occurred',
        color: 'red'
      })
    },
  })

  const updateSchedule = useMutation({
    mutationFn: ({ id, data }: { id: number; data: ScheduleEdit }) => {
      // Convert dates to ISO date strings
      const payload: any = { ...data }
      if (data.start) {
        payload.start = format(new Date(data.start), 'yyyy-MM-dd')
      }
      if (data.end) {
        payload.end = format(new Date(data.end), 'yyyy-MM-dd')
      }
      return apiFetch<Schedule>(`/schedules/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.add({ title: 'Schedule updated successfully', color: 'green' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to update schedule',
        description: error.detail || 'An error occurred',
        color: 'red'
      })
    },
  })

  const deleteSchedule = useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/schedules/${id}`, {
      method: 'DELETE',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.add({ title: 'Schedule deleted successfully', color: 'success' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to delete schedule',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  return {
    createSchedule,
    updateSchedule,
    deleteSchedule,
  }
}
