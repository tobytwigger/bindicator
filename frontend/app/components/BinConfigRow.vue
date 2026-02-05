<template>
  <div class="bin-config-row">
    <div class="bin-sketch">
      <!-- Simple bin sketch/icon -->
      <Icon name="material-symbols:delete-outline" :style="{ color: bin.color, fontSize: '40px' }" />
    </div>
    <div class="bin-details">
      <UInput v-model="localName" placeholder="Bin name" size="small" @blur="emitUpdate" />
      <UColorPicker v-model="localColor" size="small" @change="emitUpdate" />
    </div>
    <div class="bin-drag-handle">
      <Icon name="material-symbols:drag-indicator" style="font-size: 24px; color: #888;" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  bin: { name: string; color: string }
  index: number
}>()
const emits = defineEmits(['update'])

const localName = ref(props.bin.name)
const localColor = ref(props.bin.color)

watch([localName, localColor], () => {
  // No-op, just for reactivity
})

function emitUpdate() {
  emits('update', { name: localName.value, color: localColor.value, index: props.index })
}
</script>

<style scoped>
.bin-config-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.5rem 0;
}
.bin-sketch {
  min-width: 40px;
}
.bin-details {
  flex: 1;
  display: flex;
  gap: 1rem;
  align-items: center;
}
.bin-drag-handle {
  cursor: grab;
}
</style>
