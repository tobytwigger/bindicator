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

      <div v-else class="space-y-8">
        <!-- Display Settings Section -->
        <div>
          <div class="flex items-center gap-2 mb-4">
            <UIcon name="i-heroicons-computer-desktop" class="text-xl" />
            <h3 class="text-lg font-semibold">Display Settings</h3>
          </div>

          <UFormField
            label="Display Timeout"
            description="The screen will turn off after this period of inactivity"
            help="Choose between 10 seconds and 1 hour"
          >
            <div class="space-y-3">
              <USlider
                v-model="timeout"
                :min="10"
                :max="3600"
                :step="1"
                tooltip
              />
              <div class="flex justify-between text-xs text-gray-500 dark:text-gray-400">
                <span>10 seconds</span>
                <span class="font-medium">{{ formatTimeout(timeout) }}</span>
                <span>1 hour</span>
              </div>
            </div>
          </UFormField>
        </div>

        <!-- Bin Collection Reminders Section -->
        <div class="pt-6 border-t border-gray-200 dark:border-gray-800">
          <div class="flex items-center gap-2 mb-4">
            <UIcon name="i-heroicons-bell-alert" class="text-xl" />
            <h3 class="text-lg font-semibold">Bin Collection Reminders</h3>
          </div>

          <div class="space-y-6">
            <!-- Put out time -->
            <UFormField
              label="Time you put bins out"
              description="Set when you typically put bins out for collection"
            >
              <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                <USelect
                  v-model="putOutDayOption"
                  :items="[
                    { label: 'Day before collection', value: 'before' },
                    { label: 'On collection day', value: 'same' }
                  ]"
                  class="w-full sm:w-56"
                  size="md"
                />
                <span class="text-sm text-gray-600 dark:text-gray-400">at</span>
                <UInputTime
                  v-model="putOutTimeValue"
                  icon="i-heroicons-clock"
                  class="w-full sm:w-40"
                  size="md"
                />
              </div>
            </UFormField>

            <!-- Collection time -->
            <UFormField
              label="Collection time"
              description="When bins are typically collected on collection day"
            >
              <div class="flex flex-col sm:flex-row items-start sm:items-center gap-3">
                <span class="text-sm text-gray-600 dark:text-gray-400">On collection day at</span>
                <UInputTime
                  v-model="collectionTimeValue"
                  icon="i-heroicons-clock"
                  class="w-full sm:w-40"
                  size="md"
                />
              </div>
            </UFormField>
          </div>
        </div>

        <!-- Save Button -->
        <div class="pt-6 border-t border-gray-200 dark:border-gray-800 flex justify-end">
          <UButton
            @click="saveSettings"
            :loading="updateSettings.isPending.value"
            :disabled="!hasChanges"
            icon="i-heroicons-check"
            size="lg"
          >
            Save Changes
          </UButton>
        </div>
      </div>
    </UCard>

    <!-- Test Hardware Section -->
    <UCard class="mt-6">
      <template #header>
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-cpu-chip" class="text-xl" />
          <h3 class="text-xl font-bold">Test Hardware</h3>
        </div>
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
        <div class="flex items-center gap-2">
          <UIcon name="i-heroicons-command-line" class="text-xl" />
          <h3 class="text-xl font-bold">Remote Hardware Control</h3>
        </div>
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
import { Time } from '@internationalized/date'

const { settingsQuery } = useSettingsQuery()
const { updateSettings } = useSettingsMutations()

const timeout = ref(120)
const originalTimeout = ref(120)
const putOutDayBefore = ref(false)
const originalPutOutDayBefore = ref(false)

// Store the string values for API communication
const putOutTimeString = ref('17:00')
const originalPutOutTimeString = ref('17:00')
const collectionTimeString = ref('08:00')
const originalCollectionTimeString = ref('08:00')

// Helper function to convert string time to Time object
function timeStringToTimeValue(timeStr: string | undefined | null): Time {
  if (!timeStr) {
    return new Time(0, 0)
  }
  const parts = timeStr.split(':')
  if (parts.length !== 2) {
    return new Time(0, 0)
  }
  const [hours, minutes] = parts.map(Number)
  return new Time(hours || 0, minutes || 0)
}

// Helper function to convert Time object to string
function timeValueToString(time: Time | null | undefined): string {
  if (!time) return '00:00'
  const hours = String(time.hour).padStart(2, '0')
  const minutes = String(time.minute).padStart(2, '0')
  return `${hours}:${minutes}`
}

// Computed properties for UInputTime (converts string to Time object)
const putOutTimeValue = computed({
  get: () => timeStringToTimeValue(putOutTimeString.value),
  set: (value: Time | null | undefined) => {
    putOutTimeString.value = timeValueToString(value)
  }
})

const collectionTimeValue = computed({
  get: () => timeStringToTimeValue(collectionTimeString.value),
  set: (value: Time | null | undefined) => {
    collectionTimeString.value = timeValueToString(value)
  }
})

// Computed property for the dropdown (converts boolean to 'before'/'same')
const putOutDayOption = computed({
  get: () => putOutDayBefore.value ? 'before' : 'same',
  set: (value: string) => {
    putOutDayBefore.value = value === 'before'
  }
})

// Watch for settings data changes
watch(() => settingsQuery.data.value, (data) => {
  if (data) {
    timeout.value = data.timeout
    originalTimeout.value = data.timeout
    putOutDayBefore.value = data.put_out_day_before
    originalPutOutDayBefore.value = data.put_out_day_before
    putOutTimeString.value = data.put_out_time
    originalPutOutTimeString.value = data.put_out_time
    collectionTimeString.value = data.collection_time
    originalCollectionTimeString.value = data.collection_time
  }
}, { immediate: true })

const hasChanges = computed(() =>
  timeout.value !== originalTimeout.value ||
  putOutDayBefore.value !== originalPutOutDayBefore.value ||
  putOutTimeString.value !== originalPutOutTimeString.value ||
  collectionTimeString.value !== originalCollectionTimeString.value
)

function formatTimeout(seconds: number): string {
  if (seconds < 60) {
    return `${seconds} seconds`
  } else if (seconds < 3600) {
    const minutes = Math.floor(seconds / 60)
    return `${minutes} minute${minutes !== 1 ? 's' : ''}`
  } else {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (minutes === 0) {
      return `${hours} hour${hours !== 1 ? 's' : ''}`
    }
    return `${hours} hour${hours !== 1 ? 's' : ''} ${minutes} minute${minutes !== 1 ? 's' : ''}`
  }
}

function saveSettings() {
  updateSettings.mutate(
    {
      timeout: timeout.value,
      put_out_day_before: putOutDayBefore.value,
      put_out_time: putOutTimeString.value,
      collection_time: collectionTimeString.value
    },
    {
      onSuccess: () => {
        originalTimeout.value = timeout.value
        originalPutOutDayBefore.value = putOutDayBefore.value
        originalPutOutTimeString.value = putOutTimeString.value
        originalCollectionTimeString.value = collectionTimeString.value
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
</style>

