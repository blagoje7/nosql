<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content connection-modal">
      <div class="modal-header">
        <h2>🔌 Create Connection</h2>
      </div>

      <div class="modal-body">
        <div class="connection-preview">
          <div class="device-preview">
            <div :class="['preview-badge', sourceNode.data.device_type]">
              {{ sourceNode.data.device_type }}
            </div>
            <div class="preview-name">{{ sourceNode.data.hostname }}</div>
            <div class="preview-ip">{{ sourceNode.data.ip_address }}</div>
          </div>
          
          <div class="connection-arrow">→</div>
          
          <div class="device-preview">
            <div :class="['preview-badge', targetNode.data.device_type]">
              {{ targetNode.data.device_type }}
            </div>
            <div class="preview-name">{{ targetNode.data.hostname }}</div>
            <div class="preview-ip">{{ targetNode.data.ip_address }}</div>
          </div>
        </div>

        <div class="form-group">
          <label>{{ sourceNode.data.hostname }} Port</label>
          <select v-model="selectedSourcePort">
            <option value="">-- Select Port --</option>
            <option 
              v-for="port in availableSourcePorts" 
              :key="port.name"
              :value="port.name"
            >
              {{ port.name }} ({{ port.type }}, {{ port.speed }})
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ targetNode.data.hostname }} Port</label>
          <select v-model="selectedTargetPort">
            <option value="">-- Select Port --</option>
            <option 
              v-for="port in availableTargetPorts" 
              :key="port.name"
              :value="port.name"
            >
              {{ port.name }} ({{ port.type }}, {{ port.speed }})
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>Cable Type</label>
          <select v-model="cableType">
            <option value="Cat5e">Cat5e (up to 1Gbps)</option>
            <option value="Cat6">Cat6 (up to 10Gbps)</option>
            <option value="Cat6a">Cat6a (up to 10Gbps, 100m)</option>
            <option value="Cat7">Cat7 (up to 10Gbps)</option>
            <option value="Fiber-SM">Fiber Single-Mode</option>
            <option value="Fiber-MM">Fiber Multi-Mode</option>
            <option value="DAC">DAC (Direct Attach Copper)</option>
          </select>
        </div>

        <div class="form-group">
          <label>Speed</label>
          <select v-model="speed">
            <option value="10M">10 Mbps</option>
            <option value="100M">100 Mbps</option>
            <option value="1G">1 Gbps</option>
            <option value="10G">10 Gbps</option>
            <option value="25G">25 Gbps</option>
            <option value="40G">40 Gbps</option>
            <option value="100G">100 Gbps</option>
          </select>
        </div>

        <div class="form-group">
          <label>Duplex Mode</label>
          <select v-model="duplex">
            <option value="auto">Auto-Negotiate</option>
            <option value="full">Full Duplex</option>
            <option value="half">Half Duplex</option>
          </select>
        </div>

        <div class="connection-info">
          <div class="info-row">
            <span class="info-label">Connection:</span>
            <span class="info-value">
              {{ selectedSourcePort || '?' }} ↔ {{ selectedTargetPort || '?' }}
            </span>
          </div>
          <div class="info-row">
            <span class="info-label">Type:</span>
            <span class="info-value">{{ cableType }} @ {{ speed }} ({{ duplex }})</span>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button 
          @click="handleConnect" 
          class="btn btn-primary"
          :disabled="!selectedSourcePort || !selectedTargetPort"
        >
          Connect
        </button>
        <button @click="$emit('close')" class="btn btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'

const props = defineProps({
  sourceNode: {
    type: Object,
    required: true
  },
  targetNode: {
    type: Object,
    required: true
  },
  usedSourcePorts: {
    type: Array,
    default: () => []
  },
  usedTargetPorts: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['close', 'connect'])

const selectedSourcePort = ref('')
const selectedTargetPort = ref('')
const cableType = ref('Cat6')
const speed = ref('1G')
const duplex = ref('auto')

const availableSourcePorts = computed(() => {
  if (!props.sourceNode.data.ports) return []
  return props.sourceNode.data.ports.filter(p => !props.usedSourcePorts.includes(p.name))
})

const availableTargetPorts = computed(() => {
  if (!props.targetNode.data.ports) return []
  return props.targetNode.data.ports.filter(p => !props.usedTargetPorts.includes(p.name))
})

onMounted(() => {
  // Auto-select first available port
  if (availableSourcePorts.value.length > 0) {
    selectedSourcePort.value = availableSourcePorts.value[0].name
  }
  if (availableTargetPorts.value.length > 0) {
    selectedTargetPort.value = availableTargetPorts.value[0].name
  }
})

function handleConnect() {
  if (!selectedSourcePort.value || !selectedTargetPort.value) {
    return
  }

  emit('connect', {
    sourceNodeId: props.sourceNode.id,
    targetNodeId: props.targetNode.id,
    srcPort: selectedSourcePort.value,
    dstPort: selectedTargetPort.value,
    cableType: cableType.value,
    speed: speed.value,
    duplex: duplex.value
  })

  emit('close')
}
</script>

<style scoped>
.connection-modal {
  max-width: 600px;
}

.connection-preview {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background: #f5f9ff;
  border-radius: 8px;
  margin-bottom: 20px;
}

.device-preview {
  flex: 1;
  text-align: center;
}

.preview-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.preview-badge.router {
  background: #e3f2fd;
  color: #1976d2;
}

.preview-badge.switch {
  background: #e8f5e9;
  color: #388e3c;
}

.preview-badge.server {
  background: #fff3e0;
  color: #f57c00;
}

.preview-badge.client {
  background: #f3e5f5;
  color: #9c27b0;
}

.preview-name {
  font-weight: 600;
  font-size: 16px;
  color: #333;
  margin-bottom: 4px;
}

.preview-ip {
  font-size: 12px;
  color: #666;
  font-family: 'Courier New', monospace;
}

.connection-arrow {
  font-size: 32px;
  color: #1976d2;
  padding: 0 20px;
}

.connection-info {
  padding: 15px;
  background: #f5f5f5;
  border-radius: 6px;
  margin-top: 15px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-label {
  font-weight: 600;
  color: #666;
}

.info-value {
  color: #333;
  font-family: 'Courier New', monospace;
}

.form-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
}

.ip-preview {
  display: block;
  margin-top: 5px;
  font-size: 12px;
  color: #666;
}

.ip-val {
  color: #2e7d32;
  font-weight: bold;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.section-divider {
  height: 1px;
  background: #eee;
  margin: 15px 0;
}

.radio-group {
  display: flex;
  gap: 15px;
  margin-top: 5px;
}

.radio-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  cursor: pointer;
}

.indented {
  margin-left: 15px;
  padding-left: 10px;
  border-left: 2px solid #eee;
}

.input-with-action {
  display: flex;
  gap: 10px;
}

.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
}

.btn-outline {
  background: white;
  border: 1px solid #1976d2;
  color: #1976d2;
}
.readonly {
  background-color: #f0f0f0;
  cursor: default;
}
</style>
