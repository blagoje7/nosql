import axios from 'axios'

// Korišćenje direktnog URL-a da bi se osigurala povezanost bez potrebe za restartovanjem Vite dev servera
const API_BASE = 'http://127.0.0.1:8000/api'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Operacije Topologije
export async function saveTopologyAPI(topology) {
  const response = await api.post('/topology/save', topology)
  return response.data
}

export async function loadTopologyAPI() {
  const response = await api.get('/graph/topology')
  return response.data
}

// Operacije nad Uređajima
export async function deleteDeviceAPI(deviceKey) {
  const response = await api.delete(`/devices/${deviceKey}`)
  return response.data
}

// Operacije nad Konekcijama
export async function deleteConnectionAPI(connectionKey) {
  const response = await api.delete(`/connections/${connectionKey}`)
  return response.data
}

// Izvoz Konfiguracije
export async function exportConfigAPI(format = 'cisco', startDeviceKey = null) {
  const response = await api.post('/export/config', 
    { format, start_device_key: startDeviceKey },
    { responseType: 'blob' }
  )
  return response.data
}

// Upravljanje Bazama Podataka
export async function listDatabasesAPI() {
  const response = await api.get('/databases')
  return response.data
}

export async function createDatabaseAPI(name, description = '') {
  const response = await api.post('/databases', { name, description })
  return response.data
}

export async function connectDatabaseAPI(databaseName) {
  const response = await api.post('/databases/connect', null, { params: { database_name: databaseName } })
  return response.data
}

export async function getCurrentDatabaseAPI() {
  const response = await api.get('/databases/current')
  return response.data
}

// Operacije Evidencije Revizije
export async function getAuditLogAPI(limit = 100, action = null, entity_type = null) {
  const params = { limit }
  if (action) params.action = action
  if (entity_type) params.entity_type = entity_type
  
  const response = await api.get('/audit-log', { params })
  return response.data
}

export async function getAuditLogStatsAPI() {
  const response = await api.get('/audit-log/stats')
  return response.data
}

// Mrežna Statistika
export async function getNetworkStatisticsAPI() {
  const response = await api.get('/statistics/network')
  return response.data
}

// Analiza Putanja
export async function analyzePathsAPI(sourceKey, targetKey) {
  const response = await api.get('/paths/analyze', {
    params: { source_key: sourceKey, target_key: targetKey }
  })
  return response
}

// Provera Zdravlja
export async function healthCheckAPI() {
  const response = await api.get('/health')
  return response.data
}

export default api
