<template>
  <div class="canvas-wrapper">
    <VueFlow
      v-model:nodes="nodes"
      v-model:edges="edges"
      :default-viewport="{ zoom: 1 }"
      :min-zoom="0.2"
      :max-zoom="4"
      :pan-on-drag="true"
      :zoom-on-scroll="true"
      :zoom-on-pinch="true"
      @connect="onConnect"
      @node-click="onNodeClick"
      @node-context-menu="onNodeContextMenu"
      @edge-click="onEdgeClick"
    >
      <Background pattern-color="#aaa" :gap="16" />
      <Controls />
      <MiniMap />
      
      <template #node-custom="{ data }">
        <div :class="['custom-node', data.device_type, { 'highlighted-path': data.isPathHighlighted }]">
          <Handle type="target" :position="Position.Top" />
          <Handle type="source" :position="Position.Top" />
          
          <Handle type="target" :position="Position.Right" />
          <Handle type="source" :position="Position.Right" />
          
          <Handle type="target" :position="Position.Bottom" />
          <Handle type="source" :position="Position.Bottom" />
          
          <Handle type="target" :position="Position.Left" />
          <Handle type="source" :position="Position.Left" />

          <div class="node-header">{{ data.device_type.toUpperCase() }}</div>
          <div class="node-hostname">{{ data.hostname || 'Unnamed' }}</div>
        </div>
      </template>

      <template #node-zone="{ data }">
        <div 
          class="zone-node"
          :style="{ 
            backgroundColor: data.color || '#eef2f5',
            borderColor: data.color ? adjustColor(data.color, -40) : '#ccc'
          }"
        >
          <div class="zone-label">{{ data.hostname }}</div>
        </div>
      </template>
    </VueFlow>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { VueFlow, useVueFlow, Handle, Position } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import '@vue-flow/controls/dist/style.css'
import '@vue-flow/minimap/dist/style.css'

import { saveTopologyAPI, loadTopologyAPI, deleteDeviceAPI, deleteConnectionAPI } from '../services/api'

const emit = defineEmits(['node-click', 'connection-start', 'connection-mode-change', 'edge-click'])

const nodes = ref([])
const edges = ref([])
let nodeIdCounter = 1
let edgeIdCounter = 1

// Stanje konekcije za ručni izbor porta
const connectionMode = ref({
  active: false,
  sourceNode: null
})

const { addNodes, addEdges, removeNodes, removeEdges, onNodesChange, onEdgesChange } = useVueFlow()

// Brojač uređaja za imenovanje
const deviceCounters = {
  router: 1,
  switch: 1,
  l3_switch: 1,
  server: 1,
  client: 1,
  zone: 1
}

function generateMacAddress() {
  return Array.from({ length: 6 }, () => 
    Math.floor(Math.random() * 256).toString(16).padStart(2, '0')
  ).join(':').toUpperCase()
}

function generateIPAddress(deviceType) {
  return ''; // Nema podrazumevane IP adrese. Korisnik mora da konfiguriše ili koristi Auto-IP.
}

function addDeviceToCanvas(deviceType) {
  const nodeId = `${deviceType}_${nodeIdCounter++}`
  const hostname = `${deviceType.toUpperCase()[0]}${deviceCounters[deviceType]++}`
  
  // Upravljanje zonama
  if (deviceType === 'zone') {
    const newNode = {
      id: nodeId,
      type: 'zone',
      position: { 
        x: 200 + Math.random() * 100, 
        y: 100 + Math.random() * 100 
      },
      zIndex: -1, 
      style: { zIndex: -1 }, // Uklonjene fiksne dimenzije da bi se omogućilo menjanje veličine
      data: {
        device_type: 'zone',
        hostname: hostname,
        color: '#eef2f5',
        // Zone su vizuelna grupisanja - nemaju nevalidna mrežna svojstva
      }
    }
    addNodes([newNode])
    return
  }
  
  // Definisanje podrazumevanih portova sa tipom i brzinom
  const defaultPorts = deviceType === 'router' 
    ? [
        { name: 'eth0', type: 'ethernet', speed: '10Gbps' }, 
        { name: 'eth1', type: 'ethernet', speed: '10Gbps' }
      ]
    : deviceType === 'switch'
    ? [
        { name: 'port1', type: 'ethernet', speed: '1Gbps' }, 
        { name: 'port2', type: 'ethernet', speed: '1Gbps' }, 
        { name: 'port3', type: 'ethernet', speed: '1Gbps' }, 
        { name: 'port4', type: 'fiber', speed: '10Gbps' }
      ]
    : deviceType === 'server'
    ? [
        { name: 'eth0', type: 'ethernet', speed: '1Gbps' }
      ]
    : deviceType === 'client'
    ? [
        { name: 'eth0', type: 'ethernet', speed: '100Mbps' },
        { name: 'wifi0', type: 'wireless', speed: '300Mbps' }
      ]
    : [
        { name: 'eth0', type: 'ethernet', speed: '1Gbps' }
      ]

  const newNode = {
    id: nodeId,
    type: 'custom',
    position: { 
      x: 250 + Math.random() * 300, 
      y: 150 + Math.random() * 200 
    },
    data: {
      device_type: deviceType,
      hostname: hostname,
      mac_address: generateMacAddress(),
      ports: defaultPorts
    }
  }

  addNodes([newNode])
}

function getUsedPorts(nodeId) {
  const asSource = edges.value.filter(e => e.source === nodeId).map(e => e.data.src_port)
  const asTarget = edges.value.filter(e => e.target === nodeId).map(e => e.data.dst_port)
  return [...asSource, ...asTarget]
}

function onConnect(params) {
  // Emitovanje događaja za prikaz modala konfiguracije konekcije
  const sourceNode = nodes.value.find(n => n.id === params.source)
  const targetNode = nodes.value.find(n => n.id === params.target)
  
  if (sourceNode && targetNode) {
    emit('connection-start', {
      source: sourceNode,
      target: targetNode,
      usedSourcePorts: getUsedPorts(params.source),
      usedTargetPorts: getUsedPorts(params.target),
      params: params
    })
  }
}

function createConnection(sourceNodeId, targetNodeId, srcPort, dstPort, cableType, speed, duplex) {
  const isFiber = cableType.includes('Fiber')
  const isDAC = cableType.includes('DAC')

  const newEdge = {
    id: `edge_${edgeIdCounter++}`,
    source: sourceNodeId,
    target: targetNodeId,
    type: 'straight',
    animated: isFiber,
    label: `${srcPort} ↔ ${dstPort}`,
    style: {
      stroke: isFiber ? '#ffa500' : isDAC ? '#00bcd4' : '#666',
      strokeWidth: isFiber || isDAC ? 3 : 2,
      strokeDasharray: '0'
    },
    data: {
      src_port: srcPort,
      dst_port: dstPort,
      cable_type: cableType,
      speed: speed,
      duplex: duplex
    }
  }
  
  addEdges([newEdge])
  return newEdge
}

function updateNodePortIP(nodeId, portName, ip) {
  const node = nodes.value.find(n => n.id === nodeId)
  if (node && node.data.ports) {
    const portIndex = node.data.ports.findIndex(p => p.name === portName)
    if (portIndex !== -1) {
      // Kreiranje novog niza portova za okidanje reaktivnosti
      const newPorts = [...node.data.ports]
      newPorts[portIndex] = { ...newPorts[portIndex], ip_address: ip }
      
      node.data = {
        ...node.data,
        ports: newPorts
      }
    }
  }
}

function onNodeClick(event) {
  if (connectionMode.value.active) {
    // Logika povezivanja zasnovana na režimu
    if (!connectionMode.value.sourceNode) {
      // Izbor izvora
      connectionMode.value.sourceNode = event.node
      emit('connection-mode-change', {
        active: true,
        step: 'target'
      })
    } else {
      // Izbor cilja (mora biti različit)
      if (connectionMode.value.sourceNode.id !== event.node.id) {
        // Okidanje modala konekcije
        emit('connection-start', {
          source: connectionMode.value.sourceNode,
          target: event.node,
          params: null
        })
        
        // Resetovanje režima nakon izbora
        cancelConnectionMode()
      }
    }
  } else {
    // Standardni klik na čvor (svojstva)
    emit('node-click', event.node)
  }
}

function toggleConnectionMode() {
  connectionMode.value.active = !connectionMode.value.active
  connectionMode.value.sourceNode = null
  
  emit('connection-mode-change', {
    active: connectionMode.value.active,
    step: 'source'
  })
}

function cancelConnectionMode() {
  connectionMode.value.active = false
  connectionMode.value.sourceNode = null
  emit('connection-mode-change', {
    active: false,
    step: 'source'
  })
}

function onNodeContextMenu(event) {
  event.event.preventDefault() // Sprečavanje menija pretraživača
  if (confirm(`Delete ${event.node.data.hostname}? This will also delete connections and clear neighbor IPs.`)) {
    // Optimističko UI ažuriranje
    const nodeId = event.node.id;
    removeNodes([nodeId]);
    
    // Poziv backend-a za čišćenje baze (ignorisati 404 ako uređaj još nije sačuvan)
    deleteDeviceAPI(nodeId).catch(err => {
        if (err.response?.status === 404) {
          console.log("Device not in database (was never saved), UI deletion sufficient");
        } else {
          console.error("Failed to delete device on backend:", err);
          alert("Frontend deleted, but backend failed: " + (err.response?.data?.detail || err.message));
        }
    });
  }
}

function onEdgeClick(event) {
  const edge = event.edge
  // Emitovanje klika na ivicu za modal svojstava
  emit('edge-click', edge)
}

function deleteConnection(edgeId) {
  const edge = edges.value.find(e => e.id === edgeId)
  if (!edge) return

  // Optimističko UI ažuriranje
  removeEdges([edgeId])
  
  // Poziv backend-a za čišćenje baze i brisanje IP adresa
  deleteConnectionAPI(edgeId).catch(err => {
    console.error("Failed to delete connection on backend:", err);
    // Note: New connections not yet saved to DB might 404, which is expected.
  });
  
  // Also update local frontend state for ports immediately (visual only)
  updateNodePortIP(edge.source, edge.data.src_port, "")
  updateNodePortIP(edge.target, edge.data.dst_port, "")
}

function adjustColor(color, amount) {
  let usePound = false;
  if (color[0] === "#") {
    color = color.slice(1);
    usePound = true;
  }
  let num = parseInt(color, 16);
  let r = (num >> 16) + amount;
  if (r > 255) r = 255; else if (r < 0) r = 0;
  let b = ((num >> 8) & 0x00FF) + amount;
  if (b > 255) b = 255; else if (b < 0) b = 0;
  let g = (num & 0x0000FF) + amount;
  if (g > 255) g = 255; else if (g < 0) g = 0;
  return (usePound ? "#" : "") + (g | (b << 8) | (r << 16)).toString(16);
}

function updateNode(nodeId, newData) {
  const node = nodes.value.find(n => n.id === nodeId)
  if (node) {
    node.data = { ...node.data, ...newData }
  }
}

function getTopologyData() {
  // Transformisanje Vue Flow podataka u backend format
  const devices = nodes.value.map(node => ({
    _key: node.id,
    hostname: node.data.hostname,
    device_type: node.data.device_type,
    mac_address: node.data.mac_address,
    ports: node.data.ports,
    ui_position: node.position
  }))

  const connections = edges.value.map(edge => ({
    _key: edge.id,
    _from: `devices/${edge.source}`,
    _to: `devices/${edge.target}`,
    src_port: edge.data.src_port,
    dst_port: edge.data.dst_port,
    cable_type: edge.data.cable_type,
    speed: edge.data.speed || '1G',
    duplex: edge.data.duplex || 'auto',
    status: 'active',
    subnet: edge.data.subnet,
    src_ip: edge.data.src_ip,
    dst_ip: edge.data.dst_ip
  }))

  return { devices, connections }
}

function resetDeviceCounters() {
  // Resetovanje svih brojača uređaja na 1
  deviceCounters.router = 1
  deviceCounters.switch = 1
  deviceCounters.l3_switch = 1
  deviceCounters.server = 1
  deviceCounters.client = 1
  deviceCounters.zone = 1
}

function updateDeviceCountersFromTopology(devices) {
  // Prvo resetovanje
  resetDeviceCounters()
  
  // Pronalaženje najvećeg brojača za svaki tip uređaja
  devices.forEach(device => {
    const deviceType = device.device_type
    if (deviceCounters.hasOwnProperty(deviceType)) {
      // Ekstrakcija broja iz hostname-a (npr., "R1" -> 1, "SW2" -> 2)
      const match = device.hostname?.match(/\d+$/)
      if (match) {
        const num = parseInt(match[0])
        if (num >= deviceCounters[deviceType]) {
          deviceCounters[deviceType] = num + 1
        }
      }
    }
  })
}

function updateEdgeCounterFromTopology(connections) {
  let maxId = 0
  connections.forEach(conn => {
    // Provera da li je ID u formatu "edge_123"
    if (conn._key && conn._key.startsWith('edge_')) {
      const num = parseInt(conn._key.replace('edge_', ''))
      if (!isNaN(num) && num > maxId) {
        maxId = num
      }
    }
  })
  // Postavljamo brojač na max + 1 kako bismo izbegli kolizije
  edgeIdCounter = maxId + 1
}

function loadTopology(topologyData) {
  // Brisanje postojećeg
  nodes.value = []
  edges.value = []

  // Osiguranje da imamo nizove
  const devices = topologyData.devices || []
  const connections = topologyData.connections || []
  
  // Ažuriranje brojača uređaja na osnovu učitane topologije
  updateDeviceCountersFromTopology(devices)
  updateEdgeCounterFromTopology(connections)

  // Učitavanje uređaja
  const loadedNodes = devices.map(device => {
    const nodeType = device.device_type === 'zone' ? 'zone' : 'custom'
    return {
      id: device._key,
      type: nodeType,
      position: device.ui_position || { x: 250, y: 150 },
      // Rukovanje legacy/nedostajućim stilovima za zone
      style: device.device_type === 'zone' ? { zIndex: -1 } : {},
      zIndex: device.device_type === 'zone' ? -1 : undefined,
      data: {
        _key: device._key,
        device_type: device.device_type,
        hostname: device.hostname,
        mac_address: device.mac_address,
        router_id: device.router_id,
        color: device.color,
        ports: device.ports || [],
        subnets: device.subnets || [],
        vlans: device.vlans || [],
        static_routes: device.static_routes || []
      }
    }
  })

  nodes.value = loadedNodes

  // Učitavanje konekcija iz ravne liste
  const loadedEdges = connections.map(conn => {
    // Ekstrakcija ID-ja iz ArangoDB _id (npr., "devices/router_1" -> "router_1")
    // Ako _from/_to nedostaju (stari podaci), elegantno odustani ili preskoči
    const sourceId = conn._from ? conn._from.split('/')[1] : null
    const targetId = conn._to ? conn._to.split('/')[1] : null
    
    if (!sourceId || !targetId) return null

    const isFiber = conn.cable_type && conn.cable_type.includes('Fiber')
    const isDAC = conn.cable_type && conn.cable_type.includes('DAC')

    return {
      id: conn._key,
      source: sourceId,
      target: targetId,
      type: 'straight',
      animated: isFiber,
      label: `${conn.src_port} ↔ ${conn.dst_port}`,
      style: {
        stroke: isFiber ? '#ffa500' : isDAC ? '#00bcd4' : '#666',
        strokeWidth: isFiber || isDAC ? 3 : 2,
        strokeDasharray: '0'
      },
      data: {
        key: conn._key, // Čuvanje ključa za isticanje putanje
        src_port: conn.src_port,
        dst_port: conn.dst_port,
        cable_type: conn.cable_type || 'Cat6',
        speed: conn.speed || '1G',
        duplex: conn.duplex || 'auto',
        subnet: conn.subnet,
        src_ip: conn.src_ip,
        dst_ip: conn.dst_ip
      }
    }
  }).filter(e => e !== null)

  edges.value = loadedEdges
}

function clearCanvas() {
  nodes.value = []
  edges.value = []
  
  // Resetovanje brojača
  nodeIdCounter = 1
  edgeIdCounter = 1
  resetDeviceCounters()
}

function getNodeConnections(nodeId) {
  return edges.value.filter(edge => 
    edge.source === nodeId || edge.target === nodeId
  )
}

function removeEdge(edgeId) {
  edges.value = edges.value.filter(e => e.id !== edgeId)
}

// Čuvanje istaknutih putanja radi podrške za višestruka istovremena isticanja
const highlightedPaths = ref([])

function highlightPath(pathData) {
  if (!pathData || !pathData.path || !pathData.color) return
  
  const { path, color } = pathData
  const colorMap = {
    'green': '#34a853',
    'red': '#ea4335',
    'yellow': '#fbbc04'
  }
  const strokeColor = colorMap[color] || color
  
  // Čuvanje ove putanje za referencu
  highlightedPaths.value.push({
    deviceKeys: path.devices.map(d => d.key),
    connectionKeys: path.connections.map(c => c.key),
    color: strokeColor
  })
  
  // Primena isticanja
  applyPathHighlights()
}

function clearPathHighlights() {
  highlightedPaths.value = []
  
  // Resetovanje svih čvorova
  nodes.value = nodes.value.map(n => ({
    ...n,
    data: { ...n.data, isPathHighlighted: false },
    style: { ...n.style, opacity: 1 }
  }))
  
  // Resetovanje svih ivica na originalni stil
  edges.value = edges.value.map(e => {
    const isFiber = e.data.cable_type && e.data.cable_type.includes('Fiber')
    const isDAC = e.data.cable_type && e.data.cable_type.includes('DAC')
    
    return {
      ...e,
      animated: isFiber,
      style: {
        ...e.style,
        stroke: isFiber ? '#ffa500' : isDAC ? '#00bcd4' : '#666',
        strokeWidth: isFiber || isDAC ? 3 : 2
      }
    }
  })
}

function applyPathHighlights() {
  if (highlightedPaths.value.length === 0) {
    clearPathHighlights()
    return
  }
  
  // Zatamnjenje svih čvorova i ivica prvo
  nodes.value = nodes.value.map(n => ({
    ...n,
    data: { ...n.data, isPathHighlighted: false },
    style: { ...n.style, opacity: 0.3 }
  }))
  
  edges.value = edges.value.map(e => ({
    ...e,
    animated: false,
    style: { ...e.style, stroke: '#ddd', strokeWidth: 1 }
  }))
  
  // Isticanje čvorova i ivica za svaku putanju
  for (const pathInfo of highlightedPaths.value) {
    const nodeKeySet = new Set(pathInfo.deviceKeys)
    const connectionKeySet = new Set(pathInfo.connectionKeys)
    
    // Isticanje čvorova u ovoj putanji
    nodes.value = nodes.value.map(n => {
      if (nodeKeySet.has(n.data.key)) {
        return {
          ...n,
          data: { ...n.data, isPathHighlighted: true },
          style: { ...n.style, opacity: 1 }
        }
      }
      return n
    })
    
    // Isticanje ivica u ovoj putanji
    edges.value = edges.value.map(e => {
      if (e.data.key && connectionKeySet.has(e.data.key)) {
        return {
          ...e,
          animated: true,
          style: {
            ...e.style,
            stroke: pathInfo.color,
            strokeWidth: 5
          }
        }
      }
      return e
    })
  }
}

function updateConnectionProperties(edgeId, properties) {
  const edge = edges.value.find(e => e.id === edgeId)
  if (!edge) return

  // Ažuriranje podataka ivice
  edge.data = {
    ...edge.data,
    ...properties
  }

  // Ažuriranje vizuelnog stila na osnovu tipa kabla
  const isFiber = properties.cable_type && properties.cable_type.includes('Fiber')
  const isDAC = properties.cable_type && properties.cable_type.includes('DAC')
  
  edge.animated = isFiber
  edge.style = {
    stroke: isFiber ? '#ffa500' : isDAC ? '#00bcd4' : '#666',
    strokeWidth: isFiber || isDAC ? 3 : 2,
    strokeDasharray: '0'
  }
}

function getNodes() {
  return nodes.value
}

defineExpose({
  addDeviceToCanvas,
  updateNode,
  getTopologyData,
  loadTopology,
  clearCanvas,
  createConnection,
  toggleConnectionMode,
  cancelConnectionMode,
  getNodeConnections,
  removeEdge,
  highlightPath,
  clearPathHighlights,
  deleteConnection,
  updateConnectionProperties,
  getNodes
})
</script>

<style>
.canvas-wrapper {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.custom-node {
  padding: 10px;
  border-radius: 8px;
  background: white;
  border: 1px solid #ddd;
  min-width: 120px;
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  text-align: center;
  transition: all 0.2s;
}

.custom-node:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

.custom-node.router { border-top: 4px solid #1976d2; }
.custom-node.switch { border-top: 4px solid #388e3c; }
.custom-node.server { border-top: 4px solid #f57c00; }
.custom-node.client { border-top: 4px solid #9c27b0; }

.zone-node {
  width: 300px;
  height: 300px;
  min-width: 150px;
  min-height: 150px;
  border: 4px dashed;
  border-radius: 12px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  resize: both;
  overflow: hidden;
  box-sizing: border-box;
}

.zone-label {
  font-weight: 700;
  font-size: 18px;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* Zajednički Stilovi Čvorova */
.node-header {
  font-size: 10px;
  font-weight: bold;
  text-transform: uppercase;
  color: #666;
  margin-bottom: 4px;
}

.node-hostname {
  font-weight: bold;
  font-size: 14px;
  color: #333;
}

.node-ip {
  font-size: 11px;
  color: #888;
  font-family: 'Courier New', monospace;
}
</style>
