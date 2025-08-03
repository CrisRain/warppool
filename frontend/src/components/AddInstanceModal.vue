<template>
  <div v-if="show" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center" @click.self="close">
    <div class="relative mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
      <div class="mt-3 text-center">
        <h3 class="text-lg leading-6 font-medium text-gray-900">Add New WARP Instance</h3>
        <div class="mt-2 px-7 py-3">
          <input v-model="instance.name" type="text" placeholder="Instance Name" class="mb-3 px-3 py-2 text-gray-700 bg-white border rounded-md w-full focus:outline-none">
          <input v-model.number="instance.socks5_port" type="number" placeholder="SOCKS5 Port" class="mb-3 px-3 py-2 text-gray-700 bg-white border rounded-md w-full focus:outline-none">
        </div>
        <div class="items-center px-4 py-3">
          <button @click="submit" class="px-4 py-2 bg-blue-500 text-white text-base font-medium rounded-md w-full shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-300">
            Add Instance
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, defineProps, defineEmits } from 'vue';

const props = defineProps({
  show: Boolean,
});

const emit = defineEmits(['close', 'add-instance']);

const instance = ref({
  name: '',
  socks5_port: null,
  is_managed: true,
});

const close = () => {
  emit('close');
};

const submit = () => {
  emit('add-instance', { ...instance.value });
  instance.value = { name: '', socks5_port: null, is_managed: true }; // Reset form
  close();
};
</script>