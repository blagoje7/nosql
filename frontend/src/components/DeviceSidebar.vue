<template>
  <div class="sidebar">
    <h3 class="sidebar-title">Device Palette</h3>
    <p class="sidebar-subtitle">Drag or click to add</p>
    
    <div class="device-list">
      <!-- Router -->
      <div 
        class="device-item router"
        @click="$emit('add-device', 'router')"
        draggable="true"
      >
        <div class="device-icon">🔷</div>
        <div class="device-info">
          <div class="device-name">Router</div>
          <div class="device-desc">Core routing device</div>
        </div>
      </div>

      <!-- Switch (L2) -->
      <div 
        class="device-item switch"
        @click="$emit('add-device', 'switch')"
        draggable="true"
      >
        <div class="device-icon">🔶</div>
        <div class="device-info">
          <div class="device-name">L2 Switch</div>
          <div class="device-desc">Layer 2 switching</div>
        </div>
      </div>

      <!-- L3 Switch -->
      <div 
        class="device-item l3_switch"
        @click="$emit('add-device', 'l3_switch')"
        draggable="true"
      >
        <div class="device-icon">🔷</div>
        <div class="device-info">
          <div class="device-name">L3 Switch</div>
          <div class="device-desc">Layer 3 + routing</div>
        </div>
      </div>

      <!-- Server -->
      <div 
        class="device-item server"
        @click="$emit('add-device', 'server')"
        draggable="true"
      >
        <div class="device-icon">🖥️</div>
        <div class="device-info">
          <div class="device-name">Server</div>
          <div class="device-desc">End device/host</div>
        </div>
      </div>

      <!-- Client -->
      <div 
        class="device-item client"
        @click="$emit('add-device', 'client')"
        draggable="true"
      >
        <div class="device-icon">💻</div>
        <div class="device-info">
          <div class="device-name">Client</div>
          <div class="device-desc">PC/Workstation</div>
        </div>
      </div>

      <!-- Zone -->
      <div 
        class="device-item zone"
        @click="$emit('add-device', 'zone')"
        draggable="true"
      >
        <div class="device-icon">🔲</div>
        <div class="device-info">
          <div class="device-name">Zone</div>
          <div class="device-desc">Logical grouping</div>
        </div>
      </div>

      <div class="divider"></div>

      <!-- Connection Tool -->
      <div 
        class="device-item connection-tool"
        @click="$emit('toggle-connection-mode')"
      >
        <div class="device-icon">⚡</div>
        <div class="device-info">
          <div class="device-name">Connect</div>
          <div class="device-desc">Wire two devices</div>
        </div>
      </div>
    </div>

    <div class="sidebar-instructions">
      <h4>Instructions:</h4>
      <ul>
        <li>Click device to add to canvas</li>
        <li>Click node to edit properties</li>
        <li>Drag between nodes to connect</li>
        <li>Right-click node to delete</li>
      </ul>
    </div>

    <div class="sidebar-info">
      <div class="info-label">Database:</div>
      <div class="info-value">ArangoDB</div>
      <div class="info-label">Graph:</div>
      <div class="info-value">network_topology</div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['add-device', 'toggle-connection-mode'])
</script>

<style scoped>
.sidebar {
  width: 280px;
  background: white;
  border-right: 1px solid #ddd;
  padding: 20px;
  overflow-y: auto;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.sidebar-title {
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 5px;
  color: #333;
}

.sidebar-subtitle {
  font-size: 12px;
  color: #666;
  margin-bottom: 20px;
}

.device-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 30px;
}

.device-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  border: 2px solid #ddd;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
}

.device-item:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.device-item.router {
  border-color: #1976d2;
  background: linear-gradient(135deg, #e3f2fd 0%, #fff 100%);
}

.device-item.router:hover {
  background: #e3f2fd;
}

.device-item.switch {
  border-color: #388e3c;
  background: linear-gradient(135deg, #e8f5e9 0%, #fff 100%);
}

.device-item.switch:hover {
  background: #e8f5e9;
}

.device-item.l3_switch {
  border-color: #0277bd;
  background: linear-gradient(135deg, #e1f5fe 0%, #fff 100%);
}

.device-item.l3_switch:hover {
  background: #e1f5fe;
}

.device-item.server {
  border-color: #f57c00;
  background: linear-gradient(135deg, #fff3e0 0%, #fff 100%);
}

.device-item.server:hover {
  background: #fff3e0;
}

.device-item.client {
  border-color: #9c27b0;
  background: linear-gradient(135deg, #f3e5f5 0%, #fff 100%);
}

.device-item.client:hover {
  background: #f3e5f5;
}

.device-item.connection-tool {
  border-color: #ff9800;
  background: linear-gradient(135deg, #fff3e0 0%, #fff 100%);
}

.device-item.connection-tool:hover {
  background: #ffe0b2;
}

.divider {
  height: 1px;
  background: #ddd;
  margin: 8px 0;
}

.device-icon {
  font-size: 32px;
}

.device-info {
  flex: 1;
}

.device-name {
  font-weight: 600;
  font-size: 14px;
  color: #333;
  margin-bottom: 2px;
}

.device-desc {
  font-size: 11px;
  color: #666;
}

.sidebar-instructions {
  padding: 15px;
  background: #f5f5f5;
  border-radius: 6px;
  margin-bottom: 20px;
}

.sidebar-instructions h4 {
  font-size: 13px;
  margin-bottom: 8px;
  color: #333;
}

.sidebar-instructions ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.sidebar-instructions li {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
  padding-left: 15px;
  position: relative;
}

.sidebar-instructions li:before {
  content: '→';
  position: absolute;
  left: 0;
  color: #1976d2;
}

.sidebar-info {
  padding: 12px;
  background: #e3f2fd;
  border-radius: 6px;
  font-size: 12px;
}

.info-label {
  font-weight: 600;
  color: #1565c0;
  margin-top: 8px;
}

.info-label:first-child {
  margin-top: 0;
}

.info-value {
  color: #333;
  margin-bottom: 5px;
  font-family: 'Courier New', monospace;
}
</style>
