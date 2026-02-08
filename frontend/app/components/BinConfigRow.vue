<template>
  <div class="bin-config-row">
    <div class="drag-handle cursor-move">
      <Icon name="i-heroicons-bars-3" class="text-gray-400 text-xl" />
    </div>

    <div class="bin-sketch">
      <Icon name="i-heroicons-trash" :style="{ color: localColour, fontSize: '32px' }" />
    </div>

    <div class="bin-details">
      <UInput
        v-model="localName"
        placeholder="Bin name"
        size="md"
        @blur="emitUpdate"
        @keyup.enter="emitUpdate"
      />
      <input
        type="color"
        v-model="localColour"
        @change="emitUpdate"
        class="color-picker"
      />
    </div>

    <div class="bin-actions">
      <UButton
        icon="i-heroicons-arrow-up"
        size="sm"
        color="neutral"
        variant="ghost"
        :disabled="isFirst"
        @click="$emit('move-earlier')"
      />
      <UButton
        icon="i-heroicons-arrow-down"
        size="sm"
        color="neutral"
        variant="ghost"
        :disabled="isLast"
        @click="$emit('move-later')"
      />
      <UButton
        icon="i-heroicons-trash"
        size="sm"
        color="error"
        variant="ghost"
        @click="$emit('delete', props.bin)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { components } from '~/types/api'

type Bin = components['schemas']['Bin']

const props = defineProps<{
  bin: Bin
  isFirst: boolean
  isLast: boolean
}>()

const emit = defineEmits<{
  update: [bin: Bin, data: { name?: string; colour?: string }]
  delete: [bin: Bin]
  'move-earlier': []
  'move-later': []
}>()

const localName = ref(props.bin.name)
const localColour = ref(props.bin.colour || '#888888')

watch(() => props.bin.name, (newName) => {
  localName.value = newName
})

watch(() => props.bin.colour, (newColour) => {
  localColour.value = newColour || '#888888'
})

function emitUpdate() {
  const changes: { name?: string; colour?: string } = {}

  if (localName.value !== props.bin.name) {
    changes.name = localName.value
  }

  if (localColour.value !== props.bin.colour) {
    changes.colour = localColour.value
  }

  if (Object.keys(changes).length > 0) {
    emit('update', props.bin, changes)
  }
}
</script>

<style scoped>
.bin-config-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 1px solid rgb(229 231 235);
  border-radius: 0.5rem;
  background: white;
  transition: box-shadow 0.2s;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .bin-config-row {
    flex-direction: column;
    align-items: stretch;
    gap: 0.75rem;
  }
}

.bin-config-row:hover {
  box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
}

.dark .bin-config-row {
  background: rgb(23 23 23);
  border-color: rgb(38 38 38);
}

.drag-handle {
  display: flex;
  align-items: center;
  padding: 0.25rem;
}

@media (max-width: 640px) {
  .drag-handle {
    justify-content: center;
  }
}

.bin-sketch {
  display: flex;
  align-items: center;
  min-width: 40px;
}

@media (max-width: 640px) {
  .bin-sketch {
    justify-content: center;
  }
}

.bin-details {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

@media (max-width: 640px) {
  .bin-details {
    flex-direction: column;
    width: 100%;
    gap: 0.5rem;
  }

  .bin-details > * {
    width: 100%;
  }
}

.color-picker {
  width: 60px;
  height: 38px;
  border: 1px solid rgb(229 231 235);
  border-radius: 0.375rem;
  cursor: pointer;
}

@media (max-width: 640px) {
  .color-picker {
    width: 100%;
  }
}

.dark .color-picker {
  border-color: rgb(38 38 38);
}

.bin-actions {
  display: flex;
  gap: 0.25rem;
}

@media (max-width: 640px) {
  .bin-actions {
    justify-content: center;
    width: 100%;
    gap: 0.5rem;
  }
}
</style>

