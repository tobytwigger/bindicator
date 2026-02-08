<template>
  <div class="hardware-control">
    <!-- Connection Status -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <UBadge
          :color="connectionStatusColor"
          :label="connectionStatusText"
          size="sm"
        />
        <span v-if="isConnected && remainingTime" class="text-sm text-gray-600 dark:text-gray-400">
          Timeout: {{ formatTime(remainingTime) }}
        </span>
      </div>
      <div class="flex gap-2">
        <UButton
          v-if="!isConnected"
          @click="connect"
          :loading="isConnecting"
          size="sm"
          color="primary"
          icon="i-heroicons-play"
        >
          Start Control
        </UButton>
        <UButton
          v-else
          @click="disconnect"
          :loading="isDisconnecting"
          size="sm"
          color="primary"
          icon="i-heroicons-stop"
        >
          Disconnect
        </UButton>
      </div>
    </div>

    <!-- Offline Message -->
    <div
      v-if="connectionStatus === 'error'"
      class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg mb-4"
    >
      <div class="flex items-start gap-3">
        <UIcon name="i-heroicons-exclamation-triangle" class="text-red-500 mt-0.5" />
        <div>
          <p class="text-sm font-medium text-red-800 dark:text-red-200">
            Connection Error
          </p>
          <p class="text-sm text-red-600 dark:text-red-300 mt-1">
            {{ errorMessage }}
          </p>
        </div>
      </div>
    </div>

    <!-- Waiting for Hardware (when connected but hardware not ready) -->
    <div v-if="isConnected && !hardwareReady" class="p-6 text-center bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg mb-4">
      <UIcon name="i-heroicons-clock" class="text-4xl mb-3 text-yellow-600" />
      <p class="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">
        Waiting for Hardware
      </p>
      <p class="text-xs text-yellow-600 dark:text-yellow-300">
        Please navigate to <strong>Settings → Remote Control</strong> on the hardware device to enable control.
      </p>
    </div>

    <!-- Control Interface (only shown when connected AND hardware ready) -->
    <div v-if="isConnected && hardwareReady" class="space-y-6">
      <!-- LCD Display Control -->
      <div class="control-section">
        <h4 class="text-lg font-semibold mb-3">LCD Display</h4>
        <div class="space-y-3">
          <div class="flex items-center gap-3">
            <label class="text-sm font-medium w-16 shrink-0">Line 1:</label>
            <UInput
              v-model="lcd.line1"
              @keyup.enter="sendLcdUpdate"
              class="flex-1"
            />
          </div>
          <div class="flex items-center gap-3">
            <label class="text-sm font-medium w-16 shrink-0">Line 2:</label>
            <UInput
              v-model="lcd.line2"
              @keyup.enter="sendLcdUpdate"
              class="flex-1"
            />
          </div>
          <UButton
            @click="sendLcdUpdate"
            :loading="isSendingLcd"
            icon="i-heroicons-paper-airplane"
            class="w-full"
          >
            Update LCD
          </UButton>
        </div>
      </div>

      <!-- Light Controls -->
      <div class="control-section">
        <h4 class="text-lg font-semibold mb-3">Bin Lights</h4>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div v-for="binNum in [1, 2, 3, 4]" :key="binNum" class="bin-control">
            <label class="block text-sm font-medium mb-2">Bin {{ binNum }}</label>
            <div class="flex gap-1">
              <UButton
                @click="setLight(binNum, 'off')"
                :color="getBinLightState(binNum) === 'off' ? 'primary' : 'neutral'"
                size="xs"
                class="flex-1"
              >
                Off
              </UButton>
              <UButton
                @click="setLight(binNum, 'on')"
                :color="getBinLightState(binNum) === 'on' ? 'primary' : 'neutral'"
                size="xs"
                class="flex-1"
              >
                On
              </UButton>
              <UButton
                @click="setLight(binNum, 'phase')"
                :color="getBinLightState(binNum) === 'phase' ? 'primary' : 'neutral'"
                size="xs"
                class="flex-1"
              >
                Phase
              </UButton>
            </div>
          </div>
        </div>
      </div>

      <!-- Status Messages -->
      <div
        v-if="statusMessage"
        class="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg"
      >
        <p class="text-sm text-green-800 dark:text-green-200">
          {{ statusMessage }}
        </p>
      </div>
    </div>

    <!-- Instructions (when not connected) -->
    <div v-else class="p-6 text-center text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 rounded-lg">
      <UIcon name="i-heroicons-command-line" class="text-4xl mb-3" />
      <p class="text-sm mb-2">
        Click "Start Control" to take over the hardware device remotely.
      </p>
      <p class="text-xs">
        You'll be able to control the LCD display and bin lights in real-time.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'

const TIMEOUT_SECONDS = 300 // 5 minutes

const connectionStatus = ref<'disconnected' | 'connecting' | 'connected' | 'error'>('disconnected')
const hardwareReady = ref(false)
const errorMessage = ref<string>('')
const statusMessage = ref<string>('')
const ws = ref<WebSocket | null>(null)
const remainingTime = ref<number | null>(null)
const timeoutInterval = ref<number | null>(null)

const lcd = ref({
  line1: '',
  line2: ''
})

const lights = ref({
  bin1: 'off',
  bin2: 'off',
  bin3: 'off',
  bin4: 'off'
})

const isSendingLcd = ref(false)

const isConnecting = computed(() => connectionStatus.value === 'connecting')
const isDisconnecting = ref(false)
const isConnected = computed(() => connectionStatus.value === 'connected')

const connectionStatusColor = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'success'
    case 'connecting':
      return 'warning'
    case 'error':
      return 'error'
    default:
      return 'neutral'
  }
})

const connectionStatusText = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'Connected'
    case 'connecting':
      return 'Connecting...'
    case 'error':
      return 'Error'
    default:
      return 'Disconnected'
  }
})

function getWebSocketUrl(): string {
  const config = useRuntimeConfig()
  const apiUrl = config.public.apiUrl || '/api'

  let wsUrl: string
  if (apiUrl.startsWith('http://')) {
    wsUrl = apiUrl.replace('http://', 'ws://')
  } else if (apiUrl.startsWith('https://')) {
    wsUrl = apiUrl.replace('https://', 'wss://')
  } else {
    wsUrl = `ws://${window.location.host}${apiUrl}`
  }

  return `${wsUrl}/hardware/control`
}

function connect() {
  if (ws.value?.readyState === WebSocket.OPEN) {
    return
  }

  connectionStatus.value = 'connecting'
  errorMessage.value = ''
  statusMessage.value = ''

  try {
    const wsUrl = getWebSocketUrl()
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      console.log('Hardware control WebSocket connected')
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        if (data.status === 'connected') {
          connectionStatus.value = 'connected'
          statusMessage.value = 'Connected! Waiting for hardware...'
          startTimeoutCounter()
        } else if (data.status === 'hardware_ready') {
          hardwareReady.value = true
          statusMessage.value = 'Hardware is ready! You can now control it.'
        } else if (data.status === 'hardware_not_ready') {
          hardwareReady.value = false
          statusMessage.value = data.message || 'Please navigate to Settings > Remote Control on the hardware device'
        } else if (data.status === 'error') {
          connectionStatus.value = 'error'
          errorMessage.value = data.message || 'Unknown error occurred'
          ws.value?.close()
        } else if (data.status === 'success') {
          statusMessage.value = data.message || 'Command sent successfully'
          resetTimeout()
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err)
      }
    }

    ws.value.onerror = (error) => {
      console.error('WebSocket error:', error)
      connectionStatus.value = 'error'
      errorMessage.value = 'WebSocket connection error'
    }

    ws.value.onclose = () => {
      console.log('Hardware control WebSocket disconnected')
      if (connectionStatus.value === 'connected') {
        connectionStatus.value = 'disconnected'
      }
      stopTimeoutCounter()
      ws.value = null
    }
  } catch (err) {
    console.error('Error creating WebSocket:', err)
    connectionStatus.value = 'error'
    errorMessage.value = 'Failed to create WebSocket connection'
  }
}

async function disconnect() {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    return
  }

  isDisconnecting.value = true

  try {
    // Send disconnect command
    ws.value.send(JSON.stringify({
      type: 'disconnect'
    }))

    // Wait a moment for the command to be sent
    await new Promise(resolve => setTimeout(resolve, 500))
  } catch (err) {
    console.error('Error sending disconnect command:', err)
  } finally {
    ws.value?.close()
    ws.value = null
    connectionStatus.value = 'disconnected'
    hardwareReady.value = false
    isDisconnecting.value = false
    stopTimeoutCounter()

    // Clear the form
    lcd.value.line1 = ''
    lcd.value.line2 = ''
    lights.value = {
      bin1: 'off',
      bin2: 'off',
      bin3: 'off',
      bin4: 'off'
    }
  }
}

function sendLcdUpdate() {
  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    return
  }

  isSendingLcd.value = true

  try {
    ws.value.send(JSON.stringify({
      type: 'lcd_display',
      line1: lcd.value.line1,
      line2: lcd.value.line2
    }))
  } catch (err) {
    console.error('Error sending LCD command:', err)
    errorMessage.value = 'Failed to send LCD command'
  } finally {
    setTimeout(() => {
      isSendingLcd.value = false
    }, 300)
  }
}

function setLight(binNum: number, state: 'off' | 'on' | 'phase') {
  const binKey = `bin${binNum}` as keyof typeof lights.value
  lights.value[binKey] = state

  if (!ws.value || ws.value.readyState !== WebSocket.OPEN) {
    return
  }

  try {
    ws.value.send(JSON.stringify({
      type: 'light_control',
      lights: lights.value
    }))
  } catch (err) {
    console.error('Error sending light command:', err)
    errorMessage.value = 'Failed to send light command'
  }
}

function getBinLightState(binNum: number): string {
  const binKey = `bin${binNum}` as keyof typeof lights.value
  return lights.value[binKey]
}

function startTimeoutCounter() {
  remainingTime.value = TIMEOUT_SECONDS
  timeoutInterval.value = window.setInterval(() => {
    if (remainingTime.value !== null && remainingTime.value > 0) {
      remainingTime.value--
    } else {
      stopTimeoutCounter()
    }
  }, 1000)
}

function stopTimeoutCounter() {
  if (timeoutInterval.value !== null) {
    clearInterval(timeoutInterval.value)
    timeoutInterval.value = null
  }
  remainingTime.value = null
}

function resetTimeout() {
  remainingTime.value = TIMEOUT_SECONDS
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
  stopTimeoutCounter()
})
</script>

<style scoped>
.hardware-control {
  /* Container styling handled by parent */
}

.control-section {
  padding: 1rem;
  border: 1px solid rgb(229 231 235);
  border-radius: 0.5rem;
  background: rgb(249 250 251);
}

.dark .control-section {
  border-color: rgb(38 38 38);
  background: rgb(24 24 27);
}

.bin-control {
  /* Individual bin control styling */
}
</style>
