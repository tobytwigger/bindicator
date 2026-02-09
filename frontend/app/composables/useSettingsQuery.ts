import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import type { components } from '~/types/api'

type Settings = components['schemas']['Settings']
type SettingsEdit = components['schemas']['SettingsEdit']

export function useSettingsQuery() {
  const { apiFetch } = useApi()

  const settingsQuery = useQuery({
    queryKey: ['settings'],
    queryFn: () => apiFetch<Settings>('/settings/'),
  })

  return { settingsQuery }
}

export function useSettingsMutations() {
  const { apiFetch } = useApi()
  const queryClient = useQueryClient()
  const toast = useToast()

  const updateSettings = useMutation({
    mutationFn: (settings: SettingsEdit) => apiFetch<Settings>('/settings/', {
      method: 'POST',
      body: JSON.stringify(settings),
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast.add({ title: 'Settings updated successfully', color: 'success' })
    },
    onError: (error: any) => {
      toast.add({
        title: 'Failed to update settings',
        description: error.detail || 'An error occurred',
        color: 'error'
      })
    },
  })

  return {
    updateSettings,
  }
}
