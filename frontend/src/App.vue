<template>
  <div class="bg-gray-100 min-h-screen">
    <nav class="bg-white shadow-md p-4">
      <div class="container mx-auto flex justify-between items-center">
        <h1 class="text-xl font-bold">WARP Pool Controller</h1>
        <button @click="showAddModal = true" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
          Add Instance
        </button>
      </div>
    </nav>

    <main class="container mx-auto p-4">
      <div v-if="error" class="bg-red-200 text-red-800 p-3 rounded-md mb-4">
        {{ error }}
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <InstanceCard
          v-for="instance in instances"
          :key="instance.id"
          :status="instance"
          @reconnect="reconnectInstance"
          @check="checkInstance"
          @delete="deleteInstance"
        />
      </div>
    </main>

    <AddInstanceModal
      :show="showAddModal"
      @close="showAddModal = false"
      @add-instance="addInstance"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import InstanceCard from './components/InstanceCard.vue';
import AddInstanceModal from './components/AddInstanceModal.vue';

const instances = ref([]);
const showAddModal = ref(false);
const error = ref(null);
let socket = null;

const connectWebSocket = () => {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${wsProtocol}//${window.location.host}/ws/status`;
  
  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log('WebSocket connected');
    error.value = null;
  };

  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'initial_status' || message.type === 'status_update') {
      updateInstances(message.data);
    }
  };

  socket.onclose = () => {
    console.log('WebSocket disconnected. Reconnecting...');
    error.value = 'Connection to server lost. Attempting to reconnect...';
    setTimeout(connectWebSocket, 3000);
  };

  socket.onerror = (err) => {
    console.error('WebSocket error:', err);
    error.value = 'Failed to connect to the real-time status server.';
    socket.close();
  };
};

const updateInstances = (statusData) => {
  instances.value = statusData.sort((a, b) => a.id - b.id);
};

const apiCall = async (method, url, data = null) => {
  try {
    error.value = null;
    const response = await axios[method](url, data);
    return response.data;
  } catch (err) {
    console.error(`API Error (${method.toUpperCase()} ${url}):`, err);
    error.value = err.response?.data?.detail || err.message || 'An unknown API error occurred.';
    return null;
  }
};

const addInstance = async (instanceData) => {
  await apiCall('post', '/api/instances', instanceData);
};

const deleteInstance = async (id) => {
  if (confirm('Are you sure you want to delete this instance?')) {
    await apiCall('delete', `/api/instances/${id}`);
  }
};

const reconnectInstance = async (id) => {
  await apiCall('post', `/api/instances/${id}/reconnect`);
};

const checkInstance = async (id) => {
  await apiCall('post', `/api/instances/${id}/check`);
};

onMounted(() => {
  connectWebSocket();
});

onUnmounted(() => {
  if (socket) {
    socket.close();
  }
});
</script>
