<template>
  <div class="bins-page">
    <UCard>
      <template #header>
        <div class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
          <h2 class="text-2xl font-bold">Manage Bins</h2>
          <UButton
            icon="i-heroicons-plus"
            @click="addBin"
            :loading="createBin.isPending.value"
          >
            Add Bin
          </UButton>
        </div>
      </template>

      <div v-if="binsQuery.isLoading.value" class="space-y-4">
        <USkeleton v-for="i in 3" :key="i" class="h-20 w-full" />
      </div>

      <div v-else-if="binsQuery.isError.value" class="text-center py-8">
        <p class="text-red-500">Failed to load bins</p>
        <UButton @click="binsQuery.refetch.value" class="mt-4">Retry</UButton>
      </div>

      <div v-else-if="bins.length === 0" class="text-center py-8">
        <p class="text-gray-500 mb-4">No bins configured yet</p>
        <UButton icon="i-heroicons-plus" @click="addBin">Add Your First Bin</UButton>
      </div>

      <div v-else ref="binsContainer" class="space-y-3">
        <BinConfigRow
          v-for="bin in bins"
          :key="bin.id"
          :bin="bin"
          @update="updateBinData"
          @delete="deleteBinConfirm"
          @move-earlier="moveBinEarlier.mutate(bin.id)"
          @move-later="moveBinLater.mutate(bin.id)"
          :is-first="bin.position === 1"
          :is-last="bin.position === bins.length"
        />
      </div>
    </UCard>
  </div>
</template>

<script setup lang="ts">
import Sortable from 'sortablejs'
import type { components } from '~/types/api'

type Bin = components['schemas']['Bin']

const { binsQuery } = useBinsQuery()
const {
  createBin,
  updateBin,
  deleteBin,
  moveBinEarlier,
  moveBinLater,
  setBinPosition
} = useBinMutations()

const bins = computed(() => {
  const items = binsQuery.data.value?.items || []
  return [...items].sort((a, b) => a.position - b.position)
})

const binsContainer = ref<HTMLElement | null>(null)
let sortableInstance: Sortable | null = null

// Set up drag and drop for reordering bins
// Use watchEffect to reinitialize when bins change (after mutations)
watchEffect(() => {
  // Ensure we're in the client environment and the container exists
  if (!import.meta.client || !binsContainer.value) return

  // Depend on bins to trigger reinit when data changes
  const currentBins = bins.value
  if (currentBins.length === 0) return

  // Clean up previous instance
  if (sortableInstance) {
    sortableInstance.destroy()
  }

  // Wait for DOM to update before initializing
  nextTick(() => {
    if (!binsContainer.value) return

    sortableInstance = Sortable.create(binsContainer.value, {
      animation: 200,
      handle: '.drag-handle',
      ghostClass: 'sortable-ghost',
      dragClass: 'sortable-drag',
      onEnd: (event) => {
        const { oldIndex, newIndex } = event

        // Only update if position actually changed
        if (oldIndex !== undefined && newIndex !== undefined && oldIndex !== newIndex) {

          const movedBin = bins.value[oldIndex]
          const newPosition = newIndex + 1 // Position is 1-based

          // Update the backend with the new position
          setBinPosition.mutate({
            id: movedBin.id,
            position: newPosition
          })
        }
      },
    })
  })
})

// Clean up on unmount
onBeforeUnmount(() => {
  if (sortableInstance) {
    sortableInstance.destroy()
    sortableInstance = null
  }
})

function addBin() {
  createBin.mutate({
    name: 'New Bin',
    colour: '#888888',
  })
}

function updateBinData(bin: Bin, data: { name?: string; colour?: string }) {
  updateBin.mutate({
    id: bin.id,
    data,
  })
}

function deleteBinConfirm(bin: Bin) {
  if (confirm(`Are you sure you want to delete "${bin.name}"?`)) {
    deleteBin.mutate(bin.id)
  }
}
</script>

<style scoped>
.bins-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 0.5rem;
}

@media (min-width: 640px) {
  .bins-page {
    padding: 0 1rem;
  }
}

/* Drag and drop styles */
:deep(.sortable-ghost) {
  opacity: 0.4;
  background: rgb(243 244 246);
}

:deep(.dark .sortable-ghost) {
  background: rgb(38 38 38);
}

:deep(.sortable-drag) {
  opacity: 1;
  cursor: grabbing !important;
}

/* Add smooth transitions for bins */
:deep(.bin-config-row) {
  transition: transform 0.2s ease, opacity 0.2s ease;
}
</style>
