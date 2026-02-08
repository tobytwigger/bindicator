<template>
  <div class="settings-page">
    <UCard>
      <template #header>
        <h2 class="text-2xl font-bold">Settings</h2>
      </template>

      <div v-if="settingsQuery.isLoading.value" class="space-y-6">
        <USkeleton class="h-32 w-full" />
      </div>

      <div v-else-if="settingsQuery.isError.value" class="text-center py-8">
        <p class="text-red-500">Failed to load settings</p>
        <UButton @click="() => { settingsQuery.refetch() }" class="mt-4">Retry</UButton>
      </div>

      <div v-else class="space-y-6">
        <div class="space-y-4">
          <label class="block text-sm font-medium">Display Timeout (seconds)</label>
          <p class="text-sm text-gray-500 dark:text-gray-400">
            The screen will turn off after {{ timeout }} seconds of inactivity
          </p>
          <div class="space-y-4">
            <div class="flex items-center gap-4">
              <input
                v-model.number="timeout"
                type="range"
                min="1"
                max="3600"
                step="1"
                class="flex-1"
                @change="handleTimeoutChange"
              />
              <UInput
                v-model.number="timeout"
                type="number"
                min="1"
                max="3600"
                class="w-24"
                @blur="handleTimeoutChange"
              />
            </div>

            <div class="flex justify-between text-sm text-gray-500">
              <span>1 second</span>
              <span>1 hour (3600s)</span>
            </div>
          </div>
        </div>

        <div class="pt-4 border-t border-gray-200 dark:border-gray-800">
          <UButton
            @click="saveSettings"
            :loading="updateSettings.isPending.value"
            :disabled="!hasChanges"
          >
            Save Changes
          </UButton>
        </div>
      </div>
    </UCard>

    <!-- Test Hardware Section -->
    <UCard class="mt-6">
      <template #header>
        <h3 class="text-xl font-bold">Test Hardware</h3>
      </template>

      <div class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Monitor GPIO events in real-time. Press any button on the hardware device to see events appear below.
          This is useful for testing that all buttons and sensors are working correctly.
        </p>

        <GpioEventMonitor />
      </div>
    </UCard>

    <!-- Remote Hardware Control Section -->
    <UCard class="mt-6">
      <template #header>
        <h3 class="text-xl font-bold">Remote Hardware Control</h3>
      </template>

      <div class="space-y-4">
        <p class="text-sm text-gray-600 dark:text-gray-400">
          Take control of the hardware device remotely. You can update the LCD display and control the bin lights
          directly from your browser. The hardware will return to normal operation when you disconnect or after 5 minutes of inactivity.
        </p>

        <HardwareControl />
      </div>
    </UCard>

<!--    &lt;!&ndash; Additional Settings Section (for future expansion) &ndash;&gt;-->
<!--    <UCard class="mt-6">-->
<!--      <template #header>-->
<!--        <h3 class="text-xl font-bold">About</h3>-->
<!--      </template>-->

<!--      <div class="space-y-4 text-sm">-->
<!--        <div>-->
<!--          <p class="text-gray-600 dark:text-gray-400">-->
<!--            Bindicator helps you manage your bin collection schedule with ease.-->
<!--          </p>-->
<!--        </div>-->

<!--        <div class="pt-4 border-t border-gray-200 dark:border-gray-800">-->
<!--          <h4 class="font-semibold mb-2">Quick Tips:</h4>-->
<!--          <ul class="list-disc list-inside space-y-1 text-gray-600 dark:text-gray-400">-->
<!--            <li>Configure your bins on the Bins page</li>-->
<!--            <li>Set up schedules by dragging bins onto the calendar</li>-->
<!--            <li>Add replacement days for holidays or special collections</li>-->
<!--            <li>Adjust the timeout to control when the display turns off</li>-->
<!--          </ul>-->
<!--        </div>-->
<!--      </div>-->
<!--    </UCard>-->
  </div>
</template>

<script setup lang="ts">
const { settingsQuery } = useSettingsQuery()
const { updateSettings } = useSettingsMutations()

const timeout = ref(120)
const originalTimeout = ref(120)

// Watch for settings data changes
watch(() => settingsQuery.data.value, (data) => {
  if (data) {
    timeout.value = data.timeout
    originalTimeout.value = data.timeout
  }
}, { immediate: true })

const hasChanges = computed(() => timeout.value !== originalTimeout.value)

function handleTimeoutChange() {
  // Ensure timeout is within bounds
  if (timeout.value < 1) timeout.value = 1
  if (timeout.value > 3600) timeout.value = 3600
}

function saveSettings() {
  updateSettings.mutate(
    { timeout: timeout.value },
    {
      onSuccess: () => {
        originalTimeout.value = timeout.value
      },
    }
  )
}
</script>

<style scoped>
.settings-page {
  max-width: 800px;
  margin: 0 auto;
}

input[type="range"] {
  -webkit-appearance: none;
  appearance: none;
  height: 6px;
  border-radius: 3px;
  background: rgb(229 231 235);
  outline: none;
}

.dark input[type="range"] {
  background: rgb(38 38 38);
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgb(132 204 22);
  cursor: pointer;
}

input[type="range"]::-moz-range-thumb {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgb(132 204 22);
  cursor: pointer;
  border: none;
}
</style>

