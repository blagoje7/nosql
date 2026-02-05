<template>
  <div class="audit-log-viewer">
    <div class="audit-header">
      <h2>📋 Audit Log</h2>
      <button @click="$emit('close')" class="close-btn">✕</button>
    </div>

    <div class="audit-stats" v-if="stats">
      <div class="stat-card">
        <div class="stat-number">{{ stats.total }}</div>
        <div class="stat-label">Total Events</div>
      </div>
      <div class="stat-card" v-for="item in stats.by_action" :key="item.action">
        <div class="stat-number">{{ item.count }}</div>
        <div class="stat-label">{{ item.action }}</div>
      </div>
    </div>

    <div class="audit-filters">
      <select v-model="filterAction" @change="loadAuditLog" class="filter-select">
        <option value="">All Actions</option>
        <option value="create">Create</option>
        <option value="update">Update</option>
        <option value="delete">Delete</option>
        <option value="bulk_save">Bulk Save</option>
      </select>

      <select v-model="filterEntityType" @change="loadAuditLog" class="filter-select">
        <option value="">All Types</option>
        <option value="device">Device</option>
        <option value="connection">Connection</option>
        <option value="topology">Topology</option>
      </select>

      <select v-model="limit" @change="loadAuditLog" class="filter-select">
        <option :value="50">Last 50</option>
        <option :value="100">Last 100</option>
        <option :value="500">Last 500</option>
      </select>

      <button @click="loadAuditLog" class="refresh-btn">🔄 Refresh</button>
    </div>

    <div class="audit-entries" v-if="entries.length > 0">
      <div 
        v-for="entry in entries" 
        :key="entry._key" 
        :class="['audit-entry', entry.action]"
      >
        <div class="entry-header">
          <span :class="['action-badge', entry.action]">{{ entry.action }}</span>
          <span class="entity-type">{{ entry.entity_type }}</span>
          <span class="entity-id">{{ entry.entity_id }}</span>
          <span class="timestamp">{{ formatTimestamp(entry.timestamp) }}</span>
        </div>
        
        <div class="entry-details" v-if="expandedEntry === entry._key">
          <div class="detail-section">
            <strong>User:</strong> {{ entry.user }}
          </div>
          <div class="detail-section">
            <strong>Database:</strong> {{ entry.database }}
          </div>
          <div class="detail-section">
            <strong>Data Snapshot:</strong>
            <pre class="data-preview">{{ JSON.stringify(entry.entity_data, null, 2) }}</pre>
          </div>
        </div>
        
        <button 
          @click="toggleExpand(entry._key)" 
          class="expand-btn"
        >
          {{ expandedEntry === entry._key ? '▲ Hide Details' : '▼ Show Details' }}
        </button>
      </div>
    </div>

    <div v-else class="no-entries">
      <p>No audit log entries found</p>
    </div>

    <div class="audit-footer">
      <p>Showing {{ entries.length }} entries</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getAuditLogAPI, getAuditLogStatsAPI } from '../services/api'

const emit = defineEmits(['close'])

const entries = ref([])
const stats = ref(null)
const filterAction = ref('')
const filterEntityType = ref('')
const limit = ref(100)
const expandedEntry = ref(null)
const loading = ref(false)

onMounted(async () => {
  await Promise.all([loadAuditLog(), loadStats()])
})

async function loadAuditLog() {
  try {
    loading.value = true
    const response = await getAuditLogAPI(
      limit.value,
      filterAction.value || null,
      filterEntityType.value || null
    )
    entries.value = response.entries
  } catch (error) {
    console.error('Failed to load audit log:', error)
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    const response = await getAuditLogStatsAPI()
    stats.value = response.statistics
  } catch (error) {
    console.error('Failed to load audit stats:', error)
  }
}

function toggleExpand(key) {
  expandedEntry.value = expandedEntry.value === key ? null : key
}

function formatTimestamp(timestamp) {
  const date = new Date(timestamp)
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.audit-log-viewer {
  position: fixed;
  right: 0;
  top: 60px;
  width: 600px;
  height: calc(100vh - 60px);
  background: white;
  box-shadow: -4px 0 15px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  z-index: 100;
  overflow: hidden;
}

.audit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom: 2px solid #5568d3;
}

.audit-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.close-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  font-size: 20px;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.audit-stats {
  display: flex;
  gap: 10px;
  padding: 15px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  overflow-x: auto;
}

.stat-card {
  background: white;
  padding: 10px 15px;
  border-radius: 8px;
  text-align: center;
  min-width: 100px;
  border: 1px solid #e0e0e0;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #667eea;
}

.stat-label {
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
  margin-top: 4px;
}

.audit-filters {
  display: flex;
  gap: 10px;
  padding: 15px;
  background: #fafafa;
  border-bottom: 1px solid #e0e0e0;
}

.filter-select {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.refresh-btn {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}

.refresh-btn:hover {
  background: #5568d3;
}

.audit-entries {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.audit-entry {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 10px;
  transition: box-shadow 0.2s;
}

.audit-entry:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.entry-header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.action-badge {
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.action-badge.create {
  background: #d4edda;
  color: #155724;
}

.action-badge.update {
  background: #fff3cd;
  color: #856404;
}

.action-badge.delete {
  background: #f8d7da;
  color: #721c24;
}

.action-badge.bulk_save {
  background: #d1ecf1;
  color: #0c5460;
}

.entity-type {
  padding: 4px 8px;
  background: #e9ecef;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.entity-id {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.timestamp {
  margin-left: auto;
  font-size: 11px;
  color: #999;
}

.entry-details {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e0e0e0;
}

.detail-section {
  margin-bottom: 10px;
  font-size: 13px;
}

.detail-section strong {
  display: block;
  margin-bottom: 4px;
  color: #333;
}

.data-preview {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
  font-size: 11px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #e0e0e0;
}

.expand-btn {
  width: 100%;
  padding: 6px;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  color: #667eea;
  margin-top: 8px;
  transition: background 0.2s;
}

.expand-btn:hover {
  background: #e9ecef;
}

.no-entries {
  text-align: center;
  padding: 40px;
  color: #999;
}

.audit-footer {
  padding: 10px 15px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
  text-align: center;
  font-size: 12px;
  color: #666;
}
</style>
