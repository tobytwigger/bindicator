<template>
  <UCard class="mt-6">
    <template #header>
      <h3 class="text-xl font-bold">All Schedules</h3>
    </template>

    <div v-if="schedulesQuery.isLoading.value">
      <USkeleton v-for="i in 3" :key="i" class="h-16 mb-2" />
    </div>

    <div v-else-if="schedules.length === 0" class="text-center py-8">
      <p class="text-gray-500">No schedules created yet</p>
    </div>

    <div v-else class="overflow-x-auto">
      <UTable
        :data="schedules"
        :columns="scheduleColumns"
      />
    </div>
  </UCard>
</template>

<script setup lang="ts">
import { h } from 'vue'
import { format, parseISO } from 'date-fns'
import type { components } from '../../types/api'

type Schedule = components['schemas']['Schedule']
type Bin = components['schemas']['Bin']

interface Props {
  bins: Bin[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  edit: [schedule: Schedule]
  delete: [schedule: Schedule]
}>()

const { schedulesQuery } = useSchedulesQuery()
const schedules = computed(() => schedulesQuery.data.value?.items || [])

// Table columns
const scheduleColumns = [
  {
    accessorKey: 'bin_id',
    header: 'Bin',
    cell: ({ row }: any) => {
      const bin = getBinById(row.getValue('bin_id'))
      return h('div', { class: 'flex items-center gap-2' }, [
        h('div', {
          class: 'w-4 h-4 rounded',
          style: { backgroundColor: bin?.colour || '#888' }
        }),
        h('span', bin?.name || 'Unknown')
      ])
    }
  },
  {
    accessorKey: 'start',
    header: 'Start Date',
    cell: ({ row }: any) => formatDate(row.getValue('start'), 'MMM d, yyyy')
  },
  {
    accessorKey: 'end',
    header: 'End Date',
    cell: ({ row }: any) => {
      const endDate = row.getValue('end')
      return endDate ? formatDate(endDate, 'MMM d, yyyy') : 'Ongoing'
    }
  },
  {
    accessorKey: 'repeat_weeks',
    header: 'Repeat',
    cell: ({ row }: any) => {
      const weeks = row.getValue('repeat_weeks')
      return `Every ${weeks} ${weeks === 1 ? 'week' : 'weeks'}`
    }
  },
  {
    accessorKey: 'actions',
    header: 'Actions',
    cell: ({ row }: any) => {
      const ButtonComponent = resolveComponent('UButton')
      return h('div', { class: 'flex gap-2' }, [
        h(ButtonComponent, {
          icon: 'i-heroicons-pencil',
          size: 'sm',
          color: 'neutral',
          variant: 'ghost',
          onClick: () => emit('edit', row.original)
        }),
        h(ButtonComponent, {
          icon: 'i-heroicons-trash',
          size: 'sm',
          color: 'error',
          variant: 'ghost',
          onClick: () => emit('delete', row.original)
        })
      ])
    }
  }
]

// Helpers
function getBinById(id: number) {
  return props.bins.find((b: Bin) => b.id === id)
}

function formatDate(date: string | Date, formatStr: string) {
  try {
    const d = typeof date === 'string' ? parseISO(date) : date
    return format(d, formatStr)
  } catch {
    return 'Invalid date'
  }
}
</script>
