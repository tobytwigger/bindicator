<template>
  <UCard title="Configure Your Bins" class="settings-card">
    <div class="bins-list">
      <div v-for="(bin, idx) in bins" :key="idx" class="bin-row">
        <BinConfigRow :bin="bin" :index="idx" @update="updateBin" />
        <UButton size="sm" type="button" @click="removeBin(idx)">Remove</UButton>
      </div>
      <UDivider />
      <UButton class="primary" @click="addBin">Add Bin</UButton>
    </div>
  </UCard>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import BinConfigRow from '../components/BinConfigRow.vue'

interface Bin {
  name: string
  color: string
}

// Stub: initial bins
const bins = ref<Bin[]>([
  { name: 'General Waste', color: '#444' },
  { name: 'Recycling', color: '#2ecc40' },
  { name: 'Garden', color: '#ffdc00' }
])

function updateBin({ name, color, index }: { name: string; color: string; index: number }) {
  bins.value[index].name = name
  bins.value[index].color = color
}

function addBin() {
  bins.value.push({ name: 'New Bin', color: '#888' })
}

function removeBin(index: number) {
  bins.value.splice(index, 1)
}

// Stub: drag-and-drop reordering
function moveBin(from: number, to: number) {
  const bin = bins.value.splice(from, 1)[0]
  bins.value.splice(to, 0, bin)
}
</script>

<style scoped>
.settings-card {
  max-width: 600px;
  margin: 2rem auto;
}
.bins-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.bin-row {
  display: flex;
  align-items: center;
  gap: 1rem;
}
</style>
