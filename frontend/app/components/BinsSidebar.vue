<template>
  <div class="bins-sidebar">
    <h3 class="text-lg font-semibold mb-3">Bins</h3>
    <div v-if="isLoading">
      <USkeleton v-for="i in 3" :key="i" class="h-12 mb-2" />
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="bin in bins"
        :key="bin.id"
        :data-bin-id="bin.id"
        :data-bin-name="bin.name"
        :data-bin-colour="bin.colour"
        class="draggable-bin"
        :style="{ borderLeftColor: bin.colour || '#888' }"
      >
        <Icon name="i-heroicons-trash" :style="{ color: bin.colour || '#888' }" />
        <span>{{ bin.name }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Draggable } from '@fullcalendar/interaction'
import type { components } from '../../types/api'

type Bin = components['schemas']['Bin']

interface Props {
  bins: Bin[]
  isLoading?: boolean
}

const props = defineProps<Props>()

// Initialize draggable bins
onMounted(() => {
  nextTick(() => {
    const containerEl = document.querySelector('.bins-sidebar') as HTMLElement
    if (containerEl) {
      new Draggable(containerEl, {
        itemSelector: '.draggable-bin',
        eventData: (eventEl) => {
          return {
            title: eventEl.dataset.binName,
            backgroundColor: eventEl.dataset.binColour,
            borderColor: eventEl.dataset.binColour,
            extendedProps: {
              binId: parseInt(eventEl.dataset.binId || '0'),
            },
          }
        },
      })
    }
  })
})
</script>

<style scoped>
.bins-sidebar {
  padding: 1rem;
  border: 1px solid rgb(229 231 235);
  border-radius: 0.5rem;
  height: fit-content;
}

.dark .bins-sidebar {
  border-color: rgb(38 38 38);
}

/* Mobile: horizontal scrolling */
@media (max-width: 767px) {
  .bins-sidebar {
    overflow-x: auto;
  }

  .bins-sidebar h3 {
    margin-bottom: 0.75rem;
  }

  .bins-sidebar .space-y-2 {
    display: flex;
    gap: 0.5rem;
    padding-bottom: 0.25rem;
  }

  /* Remove vertical spacing when in flex mode */
  .bins-sidebar .space-y-2 > * {
    margin-top: 0;
    margin-bottom: 0;
  }

  .draggable-bin {
    min-width: 120px;
    white-space: nowrap;
  }
}

.draggable-bin {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  border: 1px solid rgb(229 231 235);
  border-left: 4px solid;
  border-radius: 0.375rem;
  cursor: move;
  background: white;
  transition: box-shadow 0.2s;
}

.draggable-bin:hover {
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
}

.dark .draggable-bin {
  background: rgb(23 23 23);
  border-color: rgb(38 38 38);
}
</style>
