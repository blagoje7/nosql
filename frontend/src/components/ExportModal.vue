<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <div class="modal-header">
        <h2>📥 Export Configuration</h2>
      </div>

      <div class="modal-body">
        <p style="margin-bottom: 20px; color: #666;">
          Select the format for your network configuration export.
        </p>

        <div class="export-options">
          <div 
            v-for="option in exportOptions" 
            :key="option.format"
            :class="['export-option', { selected: selectedFormat === option.format }]"
            @click="selectedFormat = option.format"
          >
            <div class="option-icon">{{ option.icon }}</div>
            <div class="option-info">
              <div class="option-name">{{ option.name }}</div>
              <div class="option-desc">{{ option.description }}</div>
            </div>
            <div class="option-check" v-if="selectedFormat === option.format">✓</div>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="handleExport" class="btn btn-primary">
          Export
        </button>
        <button @click="$emit('close')" class="btn btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['close', 'export'])

const selectedFormat = ref('cisco')

const exportOptions = [
  {
    format: 'cisco',
    name: 'Cisco IOS Style',
    description: 'Router/switch configuration commands',
    icon: '🌐'
  },
  {
    format: 'diagram',
    name: 'Text Diagram',
    description: 'ASCII visualization of network topology',
    icon: '📊'
  },
  {
    format: 'json',
    name: 'JSON Export',
    description: 'Complete topology in JSON format',
    icon: '💾'
  }
]

function handleExport() {
  emit('export', selectedFormat.value)
}
</script>

<style scoped>
.modal-body {
  margin: 20px 0;
}

.export-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.export-option {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  border: 2px solid #ddd;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.export-option:hover {
  border-color: #1976d2;
  background: #f5f9ff;
  transform: translateX(5px);
}

.export-option.selected {
  border-color: #1976d2;
  background: #e3f2fd;
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.2);
}

.option-icon {
  font-size: 32px;
}

.option-info {
  flex: 1;
}

.option-name {
  font-weight: 600;
  font-size: 15px;
  color: #333;
  margin-bottom: 3px;
}

.option-desc {
  font-size: 12px;
  color: #666;
}

.option-check {
  font-size: 24px;
  color: #1976d2;
  font-weight: bold;
}
</style>
