<template>
  <div class="stats-viewer">
    <div class="stats-header">
      <h2>📊 Network Statistics</h2>
      <button @click="$emit('close')" class="close-btn">✕</button>
    </div>

    <div class="stats-body" v-if="stats">
      <!-- Overview Cards -->
      <div class="stats-section">
        <h3>Overview</h3>
        <div class="stat-cards">
          <div class="stat-card primary">
            <div class="stat-icon">🖧</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.overview.total_devices }}</div>
              <div class="stat-label">Total Devices</div>
            </div>
          </div>
          <div class="stat-card success">
            <div class="stat-icon">🔗</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.overview.total_connections }}</div>
              <div class="stat-label">Connections</div>
            </div>
          </div>
          <div class="stat-card info">
            <div class="stat-icon">📈</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.overview.average_connections_per_device.toFixed(1) }}</div>
              <div class="stat-label">Avg Connections</div>
            </div>
          </div>
          <div class="stat-card warning" v-if="stats.overview.isolated_device_count > 0">
            <div class="stat-icon">⚠️</div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.overview.isolated_device_count }}</div>
              <div class="stat-label">Isolated Devices</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Devices by Type -->
      <div class="stats-section">
        <h3>Devices by Type</h3>
        <div class="device-type-list">
          <div 
            v-for="item in stats.devices_by_type" 
            :key="item.type"
            class="device-type-item"
          >
            <div class="device-type-info">
              <span class="device-icon">{{ getDeviceIcon(item.type) }}</span>
              <span class="device-type-name">{{ item.type }}</span>
            </div>
            <div class="device-type-bar">
              <div 
                class="device-type-fill"
                :style="{ width: getPercentage(item.count, stats.overview.total_devices) + '%' }"
              ></div>
            </div>
            <div class="device-type-count">{{ item.count }}</div>
          </div>
        </div>
      </div>

      <!-- Most Connected Devices -->
      <div class="stats-section" v-if="stats.most_connected_devices.length > 0">
        <h3>Most Connected Devices</h3>
        <div class="connected-list">
          <div 
            v-for="device in stats.most_connected_devices" 
            :key="device.device_key"
            class="connected-item"
          >
            <div class="connected-info">
              <span class="device-hostname">{{ device.hostname }}</span>
              <span class="device-type-badge">{{ device.device_type }}</span>
            </div>
            <div class="connection-badge">{{ device.connection_count }} connections</div>
          </div>
        </div>
      </div>

      <!-- Port Statistics -->
      <div class="stats-section" v-if="stats.port_statistics.length > 0">
        <h3>Port Statistics</h3>
        <div class="port-stats-table">
          <div class="table-row header-row">
            <div class="table-cell">Device Type</div>
            <div class="table-cell">Devices</div>
            <div class="table-cell">Total Ports</div>
            <div class="table-cell">Avg Ports/Device</div>
          </div>
          <div 
            v-for="item in stats.port_statistics" 
            :key="item.device_type"
            class="table-row"
          >
            <div class="table-cell">{{ item.device_type }}</div>
            <div class="table-cell">{{ item.device_count }}</div>
            <div class="table-cell">{{ item.total_ports }}</div>
            <div class="table-cell">{{ item.average_ports_per_device.toFixed(1) }}</div>
          </div>
        </div>
      </div>

      <!-- VLAN Statistics -->
      <div class="stats-section" v-if="stats.vlan_statistics.length > 0">
        <h3>VLAN Statistics</h3>
        <div class="vlan-stats-grid">
          <div 
            v-for="item in stats.vlan_statistics" 
            :key="item.device_type"
            class="vlan-stat-card"
          >
            <div class="vlan-type">{{ item.device_type }}</div>
            <div class="vlan-numbers">
              <span class="vlan-count">{{ item.total_vlans }} VLANs</span>
              <span class="vlan-devices">on {{ item.devices_with_vlans }} devices</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Static Route Statistics -->
      <div class="stats-section" v-if="stats.route_statistics.length > 0">
        <h3>Static Route Statistics</h3>
        <div class="route-stats-grid">
          <div 
            v-for="item in stats.route_statistics" 
            :key="item.device_type"
            class="route-stat-card"
          >
            <div class="route-type">{{ item.device_type }}</div>
            <div class="route-numbers">
              <span class="route-count">{{ item.total_routes }} routes</span>
              <span class="route-devices">on {{ item.devices_with_routes }} devices</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Connections by Cable Type -->
      <div class="stats-section" v-if="stats.connections_by_cable_type.length > 0">
        <h3>Connections by Cable Type</h3>
        <div class="cable-type-list">
          <div 
            v-for="item in stats.connections_by_cable_type" 
            :key="item.cable_type"
            class="cable-type-item"
          >
            <span class="cable-type-name">{{ item.cable_type }}</span>
            <div class="cable-type-bar">
              <div 
                class="cable-type-fill"
                :style="{ width: getPercentage(item.count, stats.overview.total_connections) + '%' }"
              ></div>
            </div>
            <span class="cable-type-count">{{ item.count }}</span>
          </div>
        </div>
      </div>

      <!-- Isolated Devices -->
      <div class="stats-section warning-section" v-if="stats.isolated_devices.length > 0">
        <h3>⚠️ Isolated Devices (No Connections)</h3>
        <div class="isolated-list">
          <div 
            v-for="device in stats.isolated_devices" 
            :key="device.key"
            class="isolated-item"
          >
            <span class="isolated-hostname">{{ device.hostname }}</span>
            <span class="isolated-type">{{ device.type }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="stats-footer">
      <button @click="loadStatistics" class="btn-refresh">🔄 Refresh</button>
      <span class="db-name">Database: {{ dbName }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getNetworkStatisticsAPI } from '../services/api'

const emit = defineEmits(['close'])

const stats = ref(null)
const dbName = ref('')
const loading = ref(false)

onMounted(() => {
  loadStatistics()
})

async function loadStatistics() {
  try {
    loading.value = true
    const response = await getNetworkStatisticsAPI()
    stats.value = response.statistics
    dbName.value = response.database
  } catch (error) {
    console.error('Failed to load network statistics:', error)
  } finally {
    loading.value = false
  }
}

function getPercentage(value, total) {
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}

function getDeviceIcon(type) {
  const icons = {
    router: '🔷',
    switch: '🔶',
    l3_switch: '🔷',
    server: '🖥️',
    client: '💻',
    pc: '💻'
  }
  return icons[type] || '📱'
}
</script>

<style scoped>
.stats-viewer {
  position: fixed;
  right: 0;
  top: 60px;
  width: 500px;
  height: calc(100vh - 60px);
  background: white;
  box-shadow: -4px 0 15px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-bottom: 2px solid #5568d3;
}

.stats-header h2 {
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

.stats-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.stats-section {
  margin-bottom: 30px;
}

.stats-section h3 {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin: 0 0 15px 0;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Stat Cards */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.stat-card {
  background: white;
  border-radius: 12px;
  padding: 15px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border: 2px solid;
}

.stat-card.primary {
  border-color: #667eea;
  background: linear-gradient(135deg, #f5f7ff 0%, #eef1ff 100%);
}

.stat-card.success {
  border-color: #4caf50;
  background: linear-gradient(135deg, #f1f8f4 0%, #e8f5e9 100%);
}

.stat-card.info {
  border-color: #2196f3;
  background: linear-gradient(135deg, #f1f8ff 0%, #e3f2fd 100%);
}

.stat-card.warning {
  border-color: #ff9800;
  background: linear-gradient(135deg, #fff8f1 0%, #fff3e0 100%);
}

.stat-icon {
  font-size: 32px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  line-height: 1;
}

.stat-label {
  font-size: 11px;
  color: #666;
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Device Type List */
.device-type-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.device-type-item {
  display: grid;
  grid-template-columns: 150px 1fr 50px;
  align-items: center;
  gap: 12px;
}

.device-type-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.device-icon {
  font-size: 20px;
}

.device-type-name {
  font-size: 13px;
  font-weight: 500;
  text-transform: capitalize;
}

.device-type-bar {
  height: 24px;
  background: #f0f0f0;
  border-radius: 12px;
  overflow: hidden;
}

.device-type-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  transition: width 0.3s ease;
}

.device-type-count {
  font-size: 14px;
  font-weight: 600;
  text-align: right;
}

/* Connected Devices */
.connected-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.connected-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.connected-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.device-hostname {
  font-weight: 600;
  font-size: 13px;
}

.device-type-badge {
  padding: 3px 8px;
  background: #e0e0e0;
  border-radius: 12px;
  font-size: 11px;
  text-transform: capitalize;
}

.connection-badge {
  padding: 4px 10px;
  background: #667eea;
  color: white;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

/* Port Statistics Table */
.port-stats-table {
  background: #f8f9fa;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e0e0e0;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1.5fr;
  gap: 10px;
  padding: 10px 15px;
}

.header-row {
  background: #667eea;
  color: white;
  font-weight: 600;
  font-size: 11px;
  text-transform: uppercase;
}

.table-row:not(.header-row) {
  border-bottom: 1px solid #e0e0e0;
}

.table-row:not(.header-row):last-child {
  border-bottom: none;
}

.table-cell {
  font-size: 13px;
}

/* VLAN & Route Stats */
.vlan-stats-grid, .route-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.vlan-stat-card, .route-stat-card {
  background: #e3f2fd;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #90caf9;
}

.vlan-type, .route-type {
  font-weight: 600;
  font-size: 12px;
  text-transform: capitalize;
  margin-bottom: 6px;
}

.vlan-numbers, .route-numbers {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.vlan-count, .route-count {
  font-size: 18px;
  font-weight: 700;
  color: #1976d2;
}

.vlan-devices, .route-devices {
  font-size: 11px;
  color: #666;
}

/* Cable Type List */
.cable-type-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.cable-type-item {
  display: grid;
  grid-template-columns: 120px 1fr 50px;
  align-items: center;
  gap: 12px;
}

.cable-type-name {
  font-size: 13px;
  font-weight: 500;
  text-transform: capitalize;
}

.cable-type-bar {
  height: 20px;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.cable-type-fill {
  height: 100%;
  background: linear-gradient(90deg, #4caf50 0%, #66bb6a 100%);
  transition: width 0.3s ease;
}

.cable-type-count {
  font-size: 14px;
  font-weight: 600;
  text-align: right;
}

/* Isolated Devices */
.warning-section {
  background: #fff8f1;
  padding: 15px;
  border-radius: 8px;
  border: 2px solid #ff9800;
}

.warning-section h3 {
  color: #f57c00;
}

.isolated-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.isolated-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  border: 1px solid #ffcc80;
}

.isolated-hostname {
  font-weight: 600;
  font-size: 13px;
}

.isolated-type {
  font-size: 12px;
  color: #666;
  text-transform: capitalize;
}

/* Footer */
.stats-footer {
  padding: 15px 20px;
  background: #f8f9fa;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.btn-refresh {
  padding: 8px 16px;
  background: #667eea;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-refresh:hover {
  background: #5568d3;
}

.db-name {
  font-size: 12px;
  color: #666;
  font-family: monospace;
}
</style>
