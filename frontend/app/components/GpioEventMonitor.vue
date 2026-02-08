<template>
  <div class="gpio-monitor">
    <!-- Connection Status Bar -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <UBadge
          :color="connectionStatusColor"
          :label="connectionStatusText"
          size="sm"
        />
        <span class="text-sm text-gray-600 dark:text-gray-400">
          {{ events.length }} event{{ events.length !== 1 ? 's' : '' }}
        </span>
      </div>
      <div class="flex gap-2">
        <UButton
          v-if="connectionStatus !== 'connected'"
          @click="connect"
          :loading="connectionStatus === 'connecting'"
          size="sm"
          color="primary"
          icon="i-heroicons-arrow-path"
        >
          Retry Connection
        </UButton>
        <UButton
          @click="clearEvents"
          size="sm"
          color="neutral"
          icon="i-heroicons-trash"
          :disabled="events.length === 0"
        >
          Clear Events
        </UButton>
      </div>
    </div>

    <!-- Offline Message -->
    <div
      v-if="connectionStatus === 'offline'"
      class="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg mb-4"
    >
      <div class="flex items-start gap-3">
        <UIcon name="i-heroicons-exclamation-triangle" class="text-red-500 mt-0.5" />
        <div>
          <p class="text-sm font-medium text-red-800 dark:text-red-200">
            MQTT Broker Offline
          </p>
          <p class="text-sm text-red-600 dark:text-red-300 mt-1">
            {{ offlineMessage || 'Cannot connect to the MQTT broker. Please ensure mosquitto is running.' }}
          </p>
        </div>
      </div>
    </div>

    <!-- Events List -->
    <div
      ref="eventsContainer"
      class="events-container border border-gray-200 dark:border-gray-700 rounded-lg overflow-y-auto bg-gray-50 dark:bg-gray-900"
    >
      <div v-if="events.length === 0" class="p-8 text-center text-gray-500 dark:text-gray-400">
        <UIcon name="i-heroicons-inbox" class="text-4xl mb-2" />
        <p class="text-sm">No events yet. Press a button on the hardware to see events appear here.</p>
      </div>

      <div v-else class="p-3 space-y-2">
        <div
          v-for="(event, index) in events"
          :key="index"
          class="event-item flex items-start gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <UBadge
            :color="getEventColor(event.event)"
            :label="formatEventName(event.event)"
            size="md"
            class="shrink-0"
          />
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 text-sm">
              <span class="text-gray-600 dark:text-gray-400 font-mono">
                {{ formatTimestamp(event.timestamp) }}
              </span>
              <span class="text-gray-400 dark:text-gray-600">•</span>
              <span class="text-gray-500 dark:text-gray-500 text-xs">
                {{ event.source }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick, computed } from 'vue'
import { format } from 'date-fns'

interface GpioEvent {
  event: string
  source: string
  timestamp: number
}

const MAX_EVENTS = 100
const RETRY_DELAYS = [5000, 10000, 30000] // 5s, 10s, 30s

const events = ref<GpioEvent[]>([])
const eventsContainer = ref<HTMLElement | null>(null)
const connectionStatus = ref<'disconnected' | 'connecting' | 'connected' | 'offline'>('disconnected')
const offlineMessage = ref<string>('')
const ws = ref<WebSocket | null>(null)
const retryCount = ref(0)
const retryTimeoutId = ref<number | null>(null)

const connectionStatusColor = computed(() => {
  switch (connectionStatus.value) {
    case 'connected':
      return 'success'
    case 'connecting':
      return 'warning'
    case 'offline':
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
    case 'offline':
      return 'Offline'
    default:
      return 'Disconnected'
  }
})

function getWebSocketUrl(): string {
  const config = useRuntimeConfig()
  const apiUrl = config.public.apiUrl || '/api'

  // Convert HTTP URL to WebSocket URL
  let wsUrl: string
  if (apiUrl.startsWith('http://')) {
    wsUrl = apiUrl.replace('http://', 'ws://')
  } else if (apiUrl.startsWith('https://')) {
    wsUrl = apiUrl.replace('https://', 'wss://')
  } else if (apiUrl.startsWith('/')) {
    // Relative URL - construct from window.location
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    wsUrl = `${protocol}//${window.location.host}${apiUrl}`
  } else {
    // Assume it's already a WebSocket URL
    wsUrl = apiUrl
  }

  return `${wsUrl}/hardware/subscribe-to-gpio`
}

function connect() {
  if (ws.value && ws.value.readyState === WebSocket.OPEN) {
    return
  }

  connectionStatus.value = 'connecting'

  try {
    const wsUrl = getWebSocketUrl()
    ws.value = new WebSocket(wsUrl)

    ws.value.onopen = () => {
      console.log('WebSocket connected')
      connectionStatus.value = 'connected'
      retryCount.value = 0 // Reset retry count on successful connection
      offlineMessage.value = ''
    }

    ws.value.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)

        // Handle status messages
        if (data.status === 'offline') {
          connectionStatus.value = 'offline'
          offlineMessage.value = data.message || 'MQTT broker is offline'
          return
        }

        if (data.status === 'connected') {
          connectionStatus.value = 'connected'
          offlineMessage.value = ''
          return
        }

        // Handle ping/keepalive
        if (data.type === 'ping') {
          return
        }

        // Handle GPIO events
        if (data.event && data.timestamp) {
          addEvent(data)
        }
      } catch (e) {
        console.error('Error parsing WebSocket message:', e)
      }
    }

    ws.value.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.value.onclose = () => {
      console.log('WebSocket closed')
      if (connectionStatus.value === 'connected' || connectionStatus.value === 'connecting') {
        connectionStatus.value = 'disconnected'
        scheduleReconnect()
      }
    }
  } catch (e) {
    console.error('Error creating WebSocket:', e)
    connectionStatus.value = 'disconnected'
    scheduleReconnect()
  }
}

function scheduleReconnect() {
  if (retryTimeoutId.value) {
    clearTimeout(retryTimeoutId.value)
  }

  const delayIndex = Math.min(retryCount.value, RETRY_DELAYS.length - 1)
  const delay = RETRY_DELAYS[delayIndex]

  console.log(`Scheduling reconnect in ${delay}ms (attempt ${retryCount.value + 1})`)

  retryTimeoutId.value = window.setTimeout(() => {
    retryCount.value++
    connect()
  }, delay)
}

function disconnect() {
  if (retryTimeoutId.value) {
    clearTimeout(retryTimeoutId.value)
    retryTimeoutId.value = null
  }

  if (ws.value) {
    ws.value.close()
    ws.value = null
  }

  connectionStatus.value = 'disconnected'
}

function addEvent(event: GpioEvent) {
  events.value.push(event)

  // Limit to MAX_EVENTS
  if (events.value.length > MAX_EVENTS) {
    events.value.shift()
  }

  // Auto-scroll to bottom
  nextTick(() => {
    if (eventsContainer.value) {
      eventsContainer.value.scrollTop = eventsContainer.value.scrollHeight
    }
  })
}

function clearEvents() {
  events.value = []
}

function formatEventName(eventName: string): string {
  // Convert MOVEMENT_DETECTED to "Movement Detected"
  return eventName
    .split('_')
    .map(word => word.charAt(0) + word.slice(1).toLowerCase())
    .join(' ')
}

function formatTimestamp(timestamp: number): string {
  // Convert Unix timestamp to human-readable format
  const date = new Date(timestamp * 1000)
  return format(date, 'HH:mm:ss.SSS')
}

function getEventColor(eventName: string): string {
  if (eventName.includes('BUTTON') || eventName.includes('BIN')) {
    return 'green'
  } else if (eventName.includes('MOVEMENT')) {
    return 'info'
  } else {
    return 'neutral'
  }
}

onMounted(() => {
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.gpio-monitor {
  width: 100%;
}

.events-container {
  height: 400px;
  max-height: 400px;
}

.event-item {
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
