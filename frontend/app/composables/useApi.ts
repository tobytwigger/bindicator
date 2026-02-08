import type { paths } from '~/types/api'

type ApiPaths = paths
type ApiResponse<T> = T extends { responses: { 200: { content: { 'application/json': infer R } } } } ? R : never

export interface ApiError {
  detail?: string | Array<{ loc: string[]; msg: string; type: string }>
}

export function useApi() {
  const config = useRuntimeConfig()
  const apiUrl = config.public.apiUrl || '/api'

  async function apiFetch<T>(
    url: string,
    options?: RequestInit
  ): Promise<T> {
    try {
      const response = await fetch(`${apiUrl}${url}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      })

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'An error occurred' }))
        throw error
      }

      if (response.status === 204) {
        return undefined as T
      }

      return await response.json()
    } catch (error: any) {
      throw error
    }
  }

  return { apiFetch }
}
