<template>
  <UCard class="mt-6">
    <template #header>
      <h3 class="text-xl font-bold">Holiday Schedules</h3>
    </template>

    <div v-if="replacementsQuery.isLoading.value">
      <USkeleton v-for="i in 3" :key="i" class="h-16 mb-2" />
    </div>

    <div v-else-if="replacements.length === 0" class="text-center py-8">
      <p class="text-gray-500">No holiday schedules created yet</p>
    </div>

    <div v-else class="overflow-x-auto">
      <UTable
        :data="replacements"
        :columns="replacementColumns"
      />
    </div>
  </UCard>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { format, parseISO } from 'date-fns'
import type { components } from '../../types/api'

type BinDayReplacement = components['schemas']['BinDayReplacement']

const emit = defineEmits<{
  delete: [replacement: BinDayReplacement]
}>()

const { replacementsQuery } = useBinDayReplacementsQuery()
const replacements = computed(() => replacementsQuery.data.value?.items || [])

// Table columns
const replacementColumns = [
  {
    accessorKey: 'replace',
    header: 'Normal Collection Date',
    cell: ({ row }: any) => formatDate(row.getValue('replace'), 'MMM d, yyyy')
  },
  {
    accessorKey: 'replace_with',
    header: 'New Collection Date',
    cell: ({ row }: any) => formatDate(row.getValue('replace_with'), 'MMM d, yyyy')
  },
  {
    accessorKey: 'actions',
    header: 'Actions',
    cell: ({ row }: any) => {
      const ButtonComponent = resolveComponent('UButton')
      return h(ButtonComponent, {
        icon: 'i-heroicons-trash',
        size: 'sm',
        color: 'error',
        variant: 'ghost',
        onClick: () => emit('delete', row.original)
      })
    }
  }
]

// Helpers
function formatDate(date: string | Date, formatStr: string) {
  try {
    const d = typeof date === 'string' ? parseISO(date) : date
    return format(d, formatStr)
  } catch {
    return 'Invalid date'
  }
}
</script>
