import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import type { components } from '~/types/api'
import { format } from 'date-fns'

type BinDayReplacement = components['schemas']['BinDayReplacement']
type BinDayReplacementCreate = components['schemas']['BinDayReplacementCreate']
type PaginationResponse = components['schemas']['PaginationResponse_BinDayReplacement_']

export function useBinDayReplacementsQuery(page = ref(1), perPage = ref(100)) {
  const { apiFetch } = useApi()

  const replacementsQuery = useQuery({
    queryKey: ['bin_day_replacements', page, perPage],
    queryFn: () => apiFetch<PaginationResponse>(`/bin_day_replacements/?page=${page.value}&per_page=${perPage.value}`),
  })

  return { replacementsQuery }
}

export function useBinDayReplacementMutations() {
  const { apiFetch } = useApi()
  const queryClient = useQueryClient()
  const toast = useToast()

  const createReplacement = useMutation({
    mutationFn: (replacement: BinDayReplacementCreate) => {
      // Convert dates to ISO date strings
      const payload = {
        replace: format(new Date(replacement.replace), 'yyyy-MM-dd'),
        replace_with: format(new Date(replacement.replace_with), 'yyyy-MM-dd'),
      }
      return apiFetch<BinDayReplacement>('/bin_day_replacements/', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bin_day_replacements'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.add({ title: 'Bin day replacement created successfully', color: 'success' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to create replacement',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  const updateReplacement = useMutation({
    mutationFn: ({ id, data }: { id: number; data: { replace?: string; replace_with?: string } }) => {
      const payload: any = {}
      if (data.replace) {
        payload.replace = format(new Date(data.replace), 'yyyy-MM-dd')
      }
      if (data.replace_with) {
        payload.replace_with = format(new Date(data.replace_with), 'yyyy-MM-dd')
      }
      return apiFetch<BinDayReplacement>(`/bin_day_replacements/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bin_day_replacements'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.add({ title: 'Bin day replacement updated successfully', color: 'success' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to update replacement',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  const deleteReplacement = useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/bin_day_replacements/${id}`, {
      method: 'DELETE',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bin_day_replacements'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.add({ title: 'Bin day replacement deleted successfully', color: 'success' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to delete replacement',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  return {
    createReplacement,
    updateReplacement,
    deleteReplacement,
  }
}
