<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content connection-props-modal">
      <div class="modal-header">
        <h2>🔌 Connection Properties</h2>
        <button @click="$emit('close')" class="close-btn">✕</button>
      </div>

      <div class="modal-body">
        <div class="connection-endpoints">
          <div class="endpoint">
            <span class="label">Source:</span>
            <span class="value">{{ sourceNode?.data.hostname }} : {{ edge.data.src_port }}</span>
          </div>
          <div class="endpoint">
            <span class="label">Target:</span>
            <span class="value">{{ targetNode?.data.hostname }} : {{ edge.data.dst_port }}</span>
          </div>
        </div>

        <div class="form-group">
          <label>Cable Type</label>
          <select v-model="formData.cable_type" class="form-input">
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
          <select v-model="formData.speed" class="form-input">
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
          <select v-model="formData.duplex" class="form-input">
            <option value="auto">Auto-Negotiate</option>
            <option value="full">Full Duplex</option>
            <option value="half">Half Duplex</option>
          </select>
        </div>

        <div class="form-group">
          <label>Status</label>
          <select v-model="formData.status" class="form-input">
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="down">Down</option>
          </select>
        </div>
      </div>

      <div class="modal-footer">
        <button @click="handleSave" class="btn btn-primary">
          Save Changes
        </button>
        <button @click="handleDelete" class="btn btn-danger">
          Delete Connection
        </button>
        <button @click="$emit('close')" class="btn btn-secondary">
          Cancel
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  edge: {
    type: Object,
    required: true
  },
  sourceNode: {
    type: Object,
    required: true
  },
  targetNode: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'save', 'delete'])

const formData = ref({
  cable_type: 'Cat6',
  speed: '1G',
  duplex: 'auto',
  status: 'active'
})

onMounted(() => {
  // Load current values from edge data
  formData.value = {
    cable_type: props.edge.data.cable_type || 'Cat6',
    speed: props.edge.data.speed || '1G',
    duplex: props.edge.data.duplex || 'auto',
    status: props.edge.data.status || 'active'
  }
})

function handleSave() {
  emit('save', {
    edgeId: props.edge.id,
    ...formData.value
  })
  emit('close')
}

function handleDelete() {
  const label = `${props.sourceNode.data.hostname}:${props.edge.data.src_port} ↔ ${props.targetNode.data.hostname}:${props.edge.data.dst_port}`
  if (confirm(`Delete connection: ${label}?`)) {
    emit('delete', props.edge.id)
    emit('close')
  }
}
</script>

<style scoped>
.connection-props-modal {
  max-width: 500px;
}

.connection-endpoints {
  background: #f5f9ff;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.endpoint {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.endpoint:last-child {
  margin-bottom: 0;
}

.endpoint .label {
  font-weight: 600;
  min-width: 70px;
  color: #555;
}

.endpoint .value {
  color: #222;
  font-family: 'Monaco', 'Courier New', monospace;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  color: #444;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
}

.modal-footer {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.btn {
  padding: 8px 16px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-primary:hover {
  background: #0056b3;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover {
  background: #c82333;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
}
</style>
