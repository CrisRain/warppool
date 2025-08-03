<template>
  <div class="bg-white rounded-lg shadow-md p-4 flex flex-col justify-between" :class="statusColorClass">
    <div>
      <div class="flex justify-between items-center mb-2">
        <h3 class="text-lg font-bold">{{ status.name }} (ID: {{ status.id }})</h3>
        <span class="px-2 py-1 text-xs font-semibold rounded-full" :class="healthBadgeClass">
          {{ status.is_healthy ? 'Healthy' : 'Unhealthy' }}
        </span>
      </div>
      <p class="text-sm text-gray-600">SOCKS5 Port: {{ status.socks5_port }}</p>
      <p class="text-sm text-gray-600">Status: {{ status.status }}</p>
      <p class="text-sm text-gray-600">IP: {{ status.ip || 'N/A' }}</p>
      <p class="text-sm text-gray-600">Latency: {{ status.latency ? `${status.latency} ms` : 'N/A' }}</p>
    </div>
    <div class="mt-4 flex justify-end space-x-2">
      <button @click="$emit('check', status.id)" class="px-3 py-1 text-sm bg-gray-200 rounded hover:bg-gray-300">Check</button>
      <button @click="$emit('reconnect', status.id)" class="px-3 py-1 text-sm bg-yellow-400 rounded hover:bg-yellow-500">Reconnect</button>
      <button @click="$emit('delete', status.id)" class="px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600">Delete</button>
    </div>
  </div>
</template>

<script setup>
import { computed, defineProps, defineEmits } from 'vue';

const props = defineProps({
  status: Object,
});

defineEmits(['reconnect', 'check', 'delete']);

const statusColorClass = computed(() => {
  if (!props.status.is_healthy) return 'border-l-4 border-red-500';
  if (props.status.status === 'Connected') return 'border-l-4 border-green-500';
  return 'border-l-4 border-gray-400';
});

const healthBadgeClass = computed(() => {
  return props.status.is_healthy ? 'bg-green-200 text-green-800' : 'bg-red-200 text-red-800';
});
</script>
