import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import type { components } from '~/types/api'
import { format } from 'date-fns'

type Bin = components['schemas']['Bin']
type BinCreate = components['schemas']['BinCreate']
type BinEdit = components['schemas']['BinEdit']
type PaginationResponse = components['schemas']['PaginationResponse_Bin_']

export function useBinsQuery(page = ref(1), perPage = ref(100)) {
  const { apiFetch } = useApi()
  const toast = useToast()

  const binsQuery = useQuery({
    queryKey: ['bins', page, perPage],
    queryFn: () => apiFetch<PaginationResponse>(`/bins/?page=${page.value}&per_page=${perPage.value}`),
  })

  return { binsQuery }
}

export function useBinMutations() {
  const { apiFetch } = useApi()
  const queryClient = useQueryClient()
  const toast = useToast()

  const createBin = useMutation({
    mutationFn: (bin: BinCreate) => apiFetch<Bin>('/bins/', {
      method: 'POST',
      body: JSON.stringify(bin),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bins'] })
      toast.add({ title: 'Bin created successfully', color: 'green' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to create bin',
        description: error.detail || 'An error occurred',
        color: 'red'
      })
    },
  })

  const updateBin = useMutation({
    mutationFn: ({ id, data }: { id: number; data: BinEdit }) =>
      apiFetch<Bin>(`/bins/${id}`, {
        method: 'PATCH',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bins'] })
      toast.add({ title: 'Bin updated successfully', color: 'green' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to update bin',
        description: error.detail || 'An error occurred',
        color: 'red'
      })
    },
  })

  const deleteBin = useMutation({
    mutationFn: (id: number) => apiFetch<void>(`/bins/${id}`, {
      method: 'DELETE',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bins'] })
      toast.add({ title: 'Bin deleted successfully', color: 'success' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to delete bin',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  const moveBinEarlier = useMutation({
    mutationFn: (id: number) => apiFetch<Bin>(`/bins/${id}/move-earlier`, {
      method: 'POST',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bins'] })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to move bin',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  const moveBinLater = useMutation({
    mutationFn: (id: number) => apiFetch<Bin>(`/bins/${id}/move-later`, {
      method: 'POST',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bins'] })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to move bin',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  const setBinPosition = useMutation({
    mutationFn: ({ id, position }: { id: number; position: number }) =>
      apiFetch<Bin>(`/bins/${id}/set-position?position=${position}`, {
        method: 'POST',
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bins'] })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to reorder bin',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  return {
    createBin,
    updateBin,
    deleteBin,
    moveBinEarlier,
    moveBinLater,
    setBinPosition,
  }
}
