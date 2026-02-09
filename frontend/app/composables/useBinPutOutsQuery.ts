import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'

export interface BinPutOut {
  id: number
  bin_id: number
  date_put_out_at: string  // ISO datetime string
  created_at: string
  updated_at: string
}

export interface BinPutOutCreate {
  bin_id: number
  date_put_out_at: string  // ISO datetime string
}

export interface PaginationResponse {
  items: BinPutOut[]
  total: number
  page: number
  per_page: number
}

export function useBinPutOutsByDateQuery(date: Ref<string | null>) {
  const { apiFetch } = useApi()

  const putOutsQuery = useQuery({
    queryKey: ['bin_put_outs', 'by_date', date],
    queryFn: () => {
      if (!date.value) {
        return Promise.resolve([])
      }
      return apiFetch<BinPutOut[]>(`/bin-put-outs/by-date?date=${date.value}`)
    },
    enabled: computed(() => !!date.value),
  })

  return { putOutsQuery }
}

export function useBinPutOutsQuery(page = ref(1), perPage = ref(100)) {
  const { apiFetch } = useApi()

  const putOutsQuery = useQuery({
    queryKey: ['bin_put_outs', page, perPage],
    queryFn: () => apiFetch<PaginationResponse>(`/bin-put-outs/?page=${page.value}&per_page=${perPage.value}`),
  })

  return { putOutsQuery }
}

export function useBinPutOutMutations() {
  const { apiFetch } = useApi()
  const queryClient = useQueryClient()
  const toast = useToast()

  const createBinPutOut = useMutation({
    mutationFn: (putOut: BinPutOutCreate) => {
      return apiFetch<BinPutOut>('/bin-put-outs/', {
        method: 'POST',
        body: JSON.stringify(putOut),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bin_put_outs'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.add({ title: 'Bin marked as put out', color: 'success' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to mark bin as put out',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  const deleteBinPutOut = useMutation({
    mutationFn: (putOutId: number) => {
      return apiFetch<void>(`/bin-put-outs/${putOutId}`, {
        method: 'DELETE',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bin_put_outs'] })
      queryClient.invalidateQueries({ queryKey: ['calendar'] })
      toast.add({ title: 'Bin put out record removed', color: 'success' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to remove bin put out record',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  return {
    createBinPutOut,
    deleteBinPutOut,
  }
}
