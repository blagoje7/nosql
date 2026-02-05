<template>
  <div class="app-container">
    <!-- Ekran za izbor baze podataka (prikazan kada baza nije izabrana) -->
    <div v-if="!currentDatabase" class="database-selection-screen">
      <div class="selection-card">
        <h1 class="selection-title">🗄️ NetGraph Provisioner</h1>
        <p class="selection-subtitle">Select or create a database to get started</p>
        
        <div class="database-list" v-if="databases.length > 0">
          <button 
            v-for="db in databases" 
            :key="db" 
            @click="selectDatabase(db)"
            class="database-item"
          >
            <span class="db-icon">📊</span>
            <span class="db-name">{{ db }}</span>
          </button>
        </div>
        
        <div class="no-databases" v-else>
          <p>No databases found. Create your first one below!</p>
        </div>
        
        <button @click="showProjectModal = true" class="btn-create-db">
          + Create New Database
        </button>
      </div>
    </div>

    <!-- Glavna Aplikacija (prikazana kada je baza izabrana) -->
    <template v-else>
      <!-- Gornja Alatna Traka -->
      <div class="toolbar">
        <div class="toolbar-left">
          <h1 class="app-title">🌐 NetGraph Provisioner</h1>
          <div class="project-selector">
            <select v-model="currentDatabase" @change="onDatabaseChange" class="project-dropdown">
              <option v-for="db in databases" :key="db" :value="db">
                {{ db }}
              </option>
            </select>
            <button @click="showProjectModal = true" class="btn-new-project" title="New Database">+</button>
          </div>
        </div>
        <div class="toolbar-right">
          <button @click="showStatistics = true" class="btn btn-info" title="View Network Statistics">
            📊 Statistics
          </button>
          <button @click="showAuditLog = true" class="btn btn-info" title="View Audit Log">
            📋 Audit Log
          </button>
          <button @click="saveTopology" class="btn btn-success">
            💾 Save Topology
          </button>
          <button @click="showExportModal = true" class="btn btn-primary">
            📥 Export Config
          </button>
          <button @click="loadTopology" class="btn btn-secondary">
            📂 Load
          </button>
          <button @click="clearCanvas" class="btn btn-danger">
            🗑️ Clear
          </button>
        </div>
      </div>

      <!-- Glavni Sadržaj -->
      <div class="main-content">
        <!-- Bočna Traka Uređaja -->
        <DeviceSidebar 
          @add-device="addDevice" 
          @toggle-connection-mode="toggleConnectionMode"
        />

        <!-- Platno -->
        <div class="canvas-container">
          <TopologyCanvas 
            ref="canvasRef"
            @node-click="handleNodeClick"
            @edge-click="handleEdgeClick"
            @connection-start="handleConnectionStart"
            @connection-mode-change="handleConnectionModeChange"
          />
          
          <!-- Indikator Režima Konekcije -->
          <div v-if="isConnectionMode" class="connection-mode-indicator">
            ⚡ Connection Mode Active: Select {{ connectionStep === 'source' ? 'Source' : 'Target' }} Device
            <button @click="cancelConnectionMode" class="btn-cancel-sm">Cancel</button>
          </div>
        </div>

        <!-- Panel Svojstava -->
        <PropertiesPanel 
          v-if="selectedNode"
          :node="selectedNode"
          :canvas="canvasRef"
          @update="updateNodeProperties"
          @close="selectedNode = null"
          @highlight-path="handleHighlightPath"
          @clear-highlights="handleClearHighlights"
        />
      </div>
    </template>

    <!-- Pregledač Mrežne Statistike -->
    <NetworkStatistics
      v-if="showStatistics"
      @close="showStatistics = false"
    />

    <!-- Pregledač Evidencije Revizije -->
    <AuditLogViewer
      v-if="showAuditLog"
      @close="showAuditLog = false"
    />

    <!-- Modal za Izvoz -->
    <ExportModal
      v-if="showExportModal"
      @close="showExportModal = false"
      @export="handleExport"
    />

    <!-- Modal za Konekcije -->
    <ConnectionModal
      v-if="showConnectionModal"
      :sourceNode="connectionData.source"
      :targetNode="connectionData.target"
      :usedSourcePorts="connectionData.usedSourcePorts"
      :usedTargetPorts="connectionData.usedTargetPorts"
      @close="showConnectionModal = false"
      @connect="handleConnection"
    />

    <!-- Modal Svojstava Konekcije -->
    <ConnectionPropertiesModal
      v-if="showConnectionPropsModal && selectedEdge"
      :edge="selectedEdge"
      :source-node="selectedEdgeSourceNode"
      :target-node="selectedEdgeTargetNode"
      @save="handleConnectionPropertiesUpdate"
      @delete="handleConnectionDelete"
      @close="showConnectionPropsModal = false"
    />

    <!-- Modal Projekta (sada za baze podataka) -->
    <ProjectModal
      v-if="showProjectModal"
      @close="showProjectModal = false"
      @create="createDatabase"
    />

    <!-- Toast Obaveštenja -->
    <div v-if="toast.show" :class="['toast', toast.type]">
      {{ toast.message }}
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import DeviceSidebar from './components/DeviceSidebar.vue'
import TopologyCanvas from './components/TopologyCanvas.vue'
import PropertiesPanel from './components/PropertiesPanelSimple.vue'
import ExportModal from './components/ExportModal.vue'
import ConnectionModal from './components/ConnectionModal.vue'
import ConnectionPropertiesModal from './components/ConnectionPropertiesModal.vue'
import ProjectModal from './components/ProjectModal.vue'
import AuditLogViewer from './components/AuditLogViewer.vue'
import NetworkStatistics from './components/NetworkStatistics.vue'
import { saveTopologyAPI, loadTopologyAPI, exportConfigAPI, listDatabasesAPI, createDatabaseAPI, connectDatabaseAPI, getCurrentDatabaseAPI } from './services/api'

const canvasRef = ref(null)
const selectedNode = ref(null)
const showExportModal = ref(false)
const showAuditLog = ref(false)
const showStatistics = ref(false)
const showConnectionModal = ref(false)
const showConnectionPropsModal = ref(false)
const selectedEdge = ref(null)
const selectedEdgeSourceNode = ref(null)
const selectedEdgeTargetNode = ref(null)
const showProjectModal = ref(false)
const databases = ref([])
const currentDatabase = ref(null)
const isConnectionMode = ref(false)
const connectionStep = ref('source') // 'source' ili 'target'
const connectionData = reactive({
  source: null,
  target: null,
  usedSourcePorts: [],
  usedTargetPorts: [],
  params: null
})

const toast = reactive({
  show: false,
  message: '',
  type: 'success'
})

function showToast(message, type = 'success') {
  toast.message = message
  toast.type = type
  toast.show = true
  setTimeout(() => {
    toast.show = false
  }, 3000)
}

function addDevice(deviceType) {
  if (canvasRef.value) {
    canvasRef.value.addDeviceToCanvas(deviceType)
    showToast(`${deviceType.toUpperCase()} added to canvas`, 'success')
  }
}

function handleConnectionStart(data) {
  connectionData.source = data.source
  connectionData.target = data.target
  connectionData.usedSourcePorts = data.usedSourcePorts || []
  connectionData.usedTargetPorts = data.usedTargetPorts || []
  connectionData.params = data.params
  showConnectionModal.value = true
}

function handleConnection(config) {
  if (canvasRef.value) {
    canvasRef.value.createConnection(
      config.sourceNodeId,
      config.targetNodeId,
      config.srcPort,
      config.dstPort,
      config.cableType,
      config.speed,
      config.duplex
    )
    showToast(`Connected ${config.srcPort} ↔ ${config.dstPort}`, 'success')
  }
}

function handleEdgeClick(edge) {
  if (!canvasRef.value) return

  // Dobijanje čvorova sa platna
  const canvas = canvasRef.value
  const topology = canvas.getTopologyData()
  
  // Pronalazak izvornog i ciljnog čvora
  const sourceNode = topology.devices.find(d => d._key === edge.source)
  const targetNode = topology.devices.find(d => d._key === edge.target)
  
  if (sourceNode && targetNode) {
    selectedEdge.value = edge
    selectedEdgeSourceNode.value = { 
      id: edge.source, 
      data: sourceNode 
    }
    selectedEdgeTargetNode.value = { 
      id: edge.target, 
      data: targetNode 
    }
    showConnectionPropsModal.value = true
  }
}

function handleConnectionPropertiesUpdate(data) {
  if (canvasRef.value) {
    canvasRef.value.updateConnectionProperties(data.edgeId, {
      cable_type: data.cable_type,
      speed: data.speed,
      duplex: data.duplex,
      status: data.status
    })
    showToast('Connection properties updated', 'success')
  }
}

function handleConnectionDelete(edgeId) {
  if (canvasRef.value) {
    canvasRef.value.deleteConnection(edgeId)
    showToast('Connection deleted', 'success')
  }
}

function handleNodeClick(node) {
  if (isConnectionMode.value) {
    // U režimu konekcije, ne biramo čvor za svojstva
    return
  }
  selectedNode.value = node
}

function toggleConnectionMode() {
  if (canvasRef.value) {
    canvasRef.value.toggleConnectionMode()
  }
}

function handleConnectionModeChange(status) {
  isConnectionMode.value = status.active
  connectionStep.value = status.step // 'source' or 'target'
}

function cancelConnectionMode() {
  if (canvasRef.value) {
    canvasRef.value.cancelConnectionMode()
  }
}

function highlightPath(nodeIds) {
    if (canvasRef.value) {
        canvasRef.value.highlightPath(nodeIds);
    }
}

function handleHighlightPath(pathData) {
  if (canvasRef.value) {
    canvasRef.value.highlightPath(pathData)
  }
}

function handleClearHighlights() {
  if (canvasRef.value) {
    canvasRef.value.clearPathHighlights()
  }
}

function updateNodeProperties(nodeId, newData, silent = false) {
  if (canvasRef.value) {
    canvasRef.value.updateNode(nodeId, newData)
    if (!silent) {
      showToast('Device properties updated', 'success')
    }
  }
}

async function loadDatabases() {
  try {
    const data = await listDatabasesAPI()
    databases.value = data.databases
  } catch (error) {
    console.error('Failed to load databases:', error)
    showToast('Failed to load databases', 'error')
  }
}

async function selectDatabase(dbName) {
  try {
    console.log(`Selecting database: ${dbName}`)
    await connectDatabaseAPI(dbName)
    currentDatabase.value = dbName
    showToast(`Connected to ${dbName}`, 'success')
    
    // Čekanje da Vue renderuje Canvas komponentu
    await nextTick()
    
    // Automatsko učitavanje topologije
    await loadTopology()
  } catch (error) {
    console.error('Failed to connect to database:', error)
    showToast('Failed to connect to database', 'error')
  }
}

async function createDatabase(databaseData) {
  try {
    console.log('Creating database:', databaseData)
    const result = await createDatabaseAPI(databaseData.name, databaseData.description)
    console.log('Database created:', result)
    
    await loadDatabases()
    
    // Automatski izbor nove baze podataka
    if (result.database) {
      await selectDatabase(result.database)
    }
    
    showProjectModal.value = false
  } catch (error) {
    console.error('Create database error:', error)
    const errorMsg = error.response?.data?.detail || 'Failed to create database'
    showToast(errorMsg, 'error')
  }
}

async function onDatabaseChange() {
  await selectDatabase(currentDatabase.value)
}

async function saveTopology() {
  try {
    if (!canvasRef.value) return
    
    const topology = canvasRef.value.getTopologyData()
    
    if (topology.devices.length === 0) {
      showToast('No devices to save', 'error')
      return
    }

    await saveTopologyAPI(topology)
    showToast(`Topology saved to ${currentDatabase.value}!`, 'success')
    
    // Ponovno učitavanje da bi se osiguralo sinhronizovanje podataka i postavljanje ključeva
    await loadTopology()
  } catch (error) {
    console.error('Save error:', error)
    showToast('Failed to save topology', 'error')
  }
}

async function loadTopology() {
  try {
    const data = await loadTopologyAPI()
    
    if (canvasRef.value && data.topology) {
      canvasRef.value.loadTopology(data.topology)
      showToast('Topology loaded successfully', 'success')
    }
  } catch (error) {
    console.error('Load error:', error)
    showToast('Failed to load topology', 'error')
  }
}

async function handleExport(format) {
  try {
    if (!canvasRef.value) {
      showToast('Canvas not initialized', 'error')
      return
    }
    
    const topology = canvasRef.value.getTopologyData()
    
    if (topology.devices.length === 0) {
      showToast('No devices in topology to export', 'error')
      return
    }
    
    // Čuvanje topologije prvo da bi se osiguralo da backend ima najnovije podatke
    await saveTopologyAPI(topology)
    
    const blob = await exportConfigAPI(format)
    
    // Kreiranje linka za preuzimanje
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    
    const fileExtensions = {
      'cisco': 'txt',
      'diagram': 'txt',
      'json': 'json'
    }
    
    a.download = `network_config.${fileExtensions[format] || 'txt'}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    showExportModal.value = false
    showToast(`Config exported as ${format.toUpperCase()}`, 'success')
  } catch (error) {
    console.error('Export error:', error)
    if (error.response && error.response.data) {
      showToast(`Export failed: ${error.response.data.detail || 'Unknown error'}`, 'error')
    } else if (error.message) {
      showToast(`Export failed: ${error.message}`, 'error')
    } else {
      showToast('Failed to export configuration', 'error')
    }
  }
}

function clearCanvas() {
  if (confirm('Clear entire canvas? This will not delete saved topology.')) {
    if (canvasRef.value) {
      canvasRef.value.clearCanvas()
      selectedNode.value = null
      showToast('Canvas cleared', 'info')
    }
  }
}

onMounted(async () => {
  console.log('NetGraph Provisioner initialized')
  await loadDatabases()
  // Pokušaj dobijanja trenutne baze podataka ako postoji
  try {
    const data = await getCurrentDatabaseAPI()
    if (data.database) {
      currentDatabase.value = data.database
      await loadTopology()
    }
  } catch (error) {
    // Baza nije povezana, korisnik mora izabrati jednu
    console.log('No database connected')
  }
})
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f5f5f5;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 25px;
  background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 15px;
}

.project-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.project-dropdown {
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.95);
  color: #333;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  min-width: 180px;
}

.project-dropdown:focus {
  outline: none;
  border-color: white;
  background: white;
}

.btn-new-project {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 50%;
  background: #4caf50;
  color: white;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.btn-new-project:hover {
  background: #45a049;
}

/* Ekran za Izbor Baze Podataka */
.database-selection-screen {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.selection-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  max-width: 600px;
  width: 100%;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.selection-title {
  font-size: 32px;
  font-weight: 700;
  color: #333;
  margin: 0 0 10px 0;
  text-align: center;
}

.selection-subtitle {
  font-size: 16px;
  color: #666;
  margin: 0 0 30px 0;
  text-align: center;
}

.database-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 30px;
  max-height: 400px;
  overflow-y: auto;
}

.database-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px 20px;
  background: #f8f9fa;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 16px;
  color: #333;
  font-weight: 500;
}

.database-item:hover {
  background: #e3f2fd;
  border-color: #1976d2;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(25, 118, 210, 0.2);
}

.db-icon {
  font-size: 24px;
}

.db-name {
  flex: 1;
  text-align: left;
}

.no-databases {
  text-align: center;
  padding: 40px 20px;
  color: #666;
  font-size: 16px;
}

.btn-create-db {
  width: 100%;
  padding: 15px 30px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-create-db:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.app-title {
  font-size: 24px;
  font-weight: 700;
  margin: 0;
}


.connection-mode-indicator {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(25, 118, 210, 0.9);
  color: white;
  padding: 10px 20px;
  border-radius: 20px;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 15px;
}

.btn-cancel-sm {
  background: rgba(255,255,255,0.2);
  border: none;
  color: white;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.btn-cancel-sm:hover {
  background: rgba(255,255,255,0.3);
}
.subtitle {
  font-size: 14px;
  opacity: 0.9;
}

.toolbar-right {
  display: flex;
  gap: 10px;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.canvas-container {
  flex: 1;
  position: relative;
  background: white;
  min-height: 0;
  overflow: hidden;
}
</style>
