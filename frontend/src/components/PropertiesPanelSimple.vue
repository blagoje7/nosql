<template>
  <div class="properties-panel">
    <div class="panel-header">
      <h3>{{ node.data.device_type.toUpperCase() }} Properties</h3>
      <button @click="$emit('close')" class="close-btn">✕</button>
    </div>

    <div class="panel-body">
      <div class="device-preview-header">
         <div :class="['preview-node-mini', node.data.device_type]">
            <span class="preview-icon">{{ getIcon(node.data.device_type) }}</span>
            <div class="preview-details">
              <span class="preview-hostname">{{ formData.hostname || node.data.device_type }}</span>
              <span class="preview-type">{{ node.data.device_type }}</span>
            </div>
         </div>
      </div>

      <div class="tabs">
        <button 
          :class="['tab-btn', { active: activeTab === 'general' }]" 
          @click="activeTab = 'general'"
        >
          General
        </button>
        <button 
          v-if="node.data.device_type !== 'zone'"
          :class="['tab-btn', { active: activeTab === 'ports' }]" 
          @click="activeTab = 'ports'"
        >
          {{ isEndDevice() ? 'NICs' : 'Ports' }} ({{ localPorts.length }})
        </button>
        <button 
          v-if="node.data.device_type !== 'zone' && !isEndDevice()"
          :class="['tab-btn', { active: activeTab === 'subnets' }]" 
          @click="activeTab = 'subnets'"
        >
          Subnets ({{ localSubnets.length }})
        </button>
        <button 
          v-if="node.data.device_type === 'switch' || node.data.device_type === 'l3_switch'"
          :class="['tab-btn', { active: activeTab === 'vlans' }]" 
          @click="activeTab = 'vlans'"
        >
          VLANs ({{ localVlans.length }})
        </button>
        <button 
          v-if="node.data.device_type === 'router' || node.data.device_type === 'l3_switch'"
          :class="['tab-btn', { active: activeTab === 'routes' }]" 
          @click="activeTab = 'routes'"
        >
          Routes ({{ localRoutes.length }})
        </button>
        <button 
          v-if="node.data.device_type !== 'zone'"
          :class="['tab-btn', { active: activeTab === 'paths' }]" 
          @click="activeTab = 'paths'"
        >
          🛣️ Paths
        </button>
      </div>

      <!-- General Tab -->
      <div v-show="activeTab === 'general'" class="tab-content">
        <div class="form-group">
          <label>Hostname *</label>
          <input 
            v-model="formData.hostname" 
            type="text" 
            placeholder="e.g., R1, SW1"
          />
        </div>

        <div class="form-group">
          <label>MAC Address</label>
          <input 
            v-model="formData.mac_address" 
            type="text" 
            placeholder="00:1A:2B:3C:4D:5E"
          />
        </div>

        <div class="form-group" v-if="node.data.device_type === 'router' || node.data.device_type === 'l3_switch'">
          <label>Router ID</label>
          <input 
            v-model="formData.router_id" 
            type="text" 
            placeholder="e.g., 1.1.1.1"
          />
          <small class="help-text">Used for OSPF, EIGRP, BGP routing protocols</small>
        </div>

        <div class="form-group" v-if="node.data.device_type === 'zone'">
          <label>Zone Color</label>
          <div class="color-picker-wrapper">
             <input 
               type="color" 
               v-model="formData.color" 
               class="color-input"
               @input="onColorChange"
             >
             <span class="color-val">{{ formData.color }}</span>
          </div>
        </div>
      </div>

      <!-- Tab Portova/NIC-ova -->
      <div v-show="activeTab === 'ports'" class="tab-content">
        
        <div class="port-list">
          <div v-for="(port, index) in localPorts" :key="index" class="port-item">
            <div class="port-header">
              <span class="port-name">{{ port.name }}</span>
              <div class="port-actions">
                <button 
                  v-if="node.data.device_type === 'router' && !isSubinterface(port.name)"
                  @click="showSubinterfaceForm(port.name)" 
                  class="btn-icon-action" 
                  title="Create Subinterface"
                >
                  ➕🏷️
                </button>
                <button 
                  v-if="node.data.device_type === 'switch' || node.data.device_type === 'l3_switch'"
                  @click="createSVI()" 
                  class="btn-icon-action" 
                  title="Create SVI (VLAN Interface)"
                >
                  ➕🌐
                </button>
                <button 
                  v-if="node.data.device_type === 'router' || node.data.device_type === 'l3_switch'"
                  @click="createLoopback()" 
                  class="btn-icon-action" 
                  title="Create Loopback Interface"
                >
                  ➕🔁
                </button>
                <button 
                  @click="editPort(index)" 
                  class="btn-icon-action" 
                  title="Edit Port"
                >
                  ✏️
                </button>
                <button 
                  @click="removePort(index)" 
                  class="btn-icon-danger" 
                  title="Remove Port"
                >
                  🗑️
                </button>
              </div>
            </div>
            <div class="port-details">
              <span :class="['badge', port.type]">{{ port.type }}</span>
              <span v-if="port.type !== 'loopback'" class="badge speed">{{ shortSpeed(port.speed) }}</span>
              <span v-if="port.is_svi" class="badge svi">SVI</span>
              <span v-if="port.type === 'loopback'" class="badge loopback">Loopback</span>
              <span v-if="port.is_routed" class="badge routed">Routed</span>
              <span v-if="port.mode" class="badge vlan-mode">{{ port.mode }}</span>
              <span v-if="port.vlan" class="badge vlan-id">VLAN {{ port.vlan }}</span>
              <span v-if="port.vlan_id" class="badge subif">VLAN {{ port.vlan_id }}</span>
              <span v-if="port.ip_address" class="badge ip">{{ port.ip_address }}</span>
            </div>
          </div>
        </div>

        <!-- Forma za Kreiranje Podinterfejsa -->
        <div v-if="showingSubinterfaceForm" class="add-port-section subinterface-form">
          <h4>🏷️ Create Subinterface on {{ subinterfaceParent }}</h4>
          
          <div class="subinterface-grid">
            <label class="form-label">VLAN ID *</label>
            <input 
              v-model.number="newSubinterface.vlan_id" 
              type="number"
              class="input-sm" 
              placeholder="e.g., 10"
            />
            
            <label class="form-label">Subinterface Name</label>
            <input 
              :value="subinterfaceName" 
              disabled
              class="input-sm" 
              style="background: #f0f0f0;"
            />
            
            <label class="form-label">IP Address *</label>
            <input 
              v-model="newSubinterface.ip_address" 
              class="input-sm" 
              placeholder="e.g., 192.168.10.1"
            />
            
            <label class="form-label">Subnet Mask</label>
            <select v-model="newSubinterface.subnet_mask" class="select-sm">
              <option value="255.255.255.252">/30 (255.255.255.252)</option>
              <option value="255.255.255.248">/29 (255.255.255.248)</option>
              <option value="255.255.255.240">/28 (255.255.255.240)</option>
              <option value="255.255.255.224">/27 (255.255.255.224)</option>
              <option value="255.255.255.192">/26 (255.255.255.192)</option>
              <option value="255.255.255.128">/25 (255.255.255.128)</option>
              <option value="255.255.255.0">/24 (255.255.255.0)</option>
              <option value="255.255.254.0">/23 (255.255.254.0)</option>
              <option value="255.255.252.0">/22 (255.255.252.0)</option>
            </select>
            
            <label class="form-label" style="grid-column: span 2;">Description (optional)</label>
            <input 
              v-model="newSubinterface.description" 
              class="input-sm" 
              placeholder="e.g., VLAN 10 Management"
              style="grid-column: span 2;"
            />
          </div>

          <div class="row-actions">
            <button 
              @click="createSubinterface" 
              class="btn-add-sm" 
              :disabled="!newSubinterface.vlan_id || !newSubinterface.ip_address"
            >
              Create Subinterface
            </button>
            <button 
              @click="cancelSubinterfaceForm" 
              class="btn-cancel-sm"
            >
              Cancel
            </button>
          </div>
        </div>

        <!-- Sekcija za dodavanje/izmenu Porta/NIC-a -->
        <div v-if="!showingSubinterfaceForm" :class="['add-port-section', { editing: editingPortIndex !== null }]">
          <h4>{{ editingPortIndex !== null ? '✏️ Edit' : '➕ Add' }} {{ isEndDevice() ? 'NIC' : 'Port' }}</h4>
          
          <div class="add-port-grid">
            <input 
              v-model="newPort.name" 
              class="input-sm" 
              :placeholder="isEndDevice() ? 'NIC Name (e.g., eth0, NIC1)' : 'Port Name (e.g., Gi0/1 or Gi0/1.10)'"
            />
            
            <select v-model="newPort.type" class="select-sm">
              <option value="ethernet">RJ45 (Ethernet)</option>
              <option value="fiber">SFP (Fiber)</option>
              <option value="sfp+">SFP+</option>
              <option value="qsfp">QSFP</option>
              <option value="rj11">RJ11 (Phone)</option>
              <option value="wireless">Wireless</option>
              <option v-if="node.data.device_type === 'router' || node.data.device_type === 'l3_switch'" value="loopback">Loopback</option>
            </select>
            
            <select v-model="newPort.speed" class="select-sm">
              <option value="10Mbps">10 Mbps</option>
              <option value="100Mbps">100 Mbps</option>
              <option value="1Gbps">1 Gbps</option>
              <option value="10Gbps">10 Gbps</option>
              <option value="25Gbps">25 Gbps</option>
              <option value="40Gbps">40 Gbps</option>
              <option value="100Gbps">100 Gbps</option>
            </select>
          </div>

          <!-- Konfiguracija VLAN-a za Svič -->
          <div v-if="node.data.device_type === 'switch' && !isEndDevice()" class="vlan-config">
            <label class="vlan-label">Switch Port Mode</label>
            <div class="vlan-config-grid">
              <select v-model="newPort.mode" class="select-sm">
                <option :value="null">None</option>
                <option value="access">Access</option>
                <option value="trunk">Trunk</option>
              </select>
              
              <input 
                v-if="newPort.mode"
                v-model="newPort.vlan" 
                class="input-sm" 
                :placeholder="newPort.mode === 'trunk' ? 'VLANs (e.g., 10,20,30-40)' : 'VLAN ID (e.g., 10)'"
              />
            </div>
          </div>

          <!-- Konfiguracija Porta L3 Sviča -->
          <div v-if="node.data.device_type === 'l3_switch' && !newPort.is_svi" class="vlan-config">
            <label class="vlan-label">Port Mode</label>
            <div class="vlan-config-grid">
              <select v-model="newPort.is_routed" class="select-sm">
                <option :value="false">Switchport (Layer 2)</option>
                <option :value="true">Routed (Layer 3)</option>
              </select>
            </div>
            
            <!-- L2 Režim - prikaz opcija VLAN-a -->
            <div v-if="!newPort.is_routed" class="vlan-config-grid" style="margin-top: 8px;">
              <select v-model="newPort.mode" class="select-sm">
                <option :value="null">None</option>
                <option value="access">Access</option>
                <option value="trunk">Trunk</option>
              </select>
              
              <input 
                v-if="newPort.mode"
                v-model="newPort.vlan" 
                class="input-sm" 
                :placeholder="newPort.mode === 'trunk' ? 'VLANs (e.g., 10,20,30-40)' : 'VLAN ID (e.g., 10)'"
              />
            </div>
          </div>

          <!-- Konfiguracija Ruter Podinterfejsa -->
          <div v-if="node.data.device_type === 'router' && isSubinterface(newPort.name)" class="vlan-config">
            <label class="vlan-label">Subinterface Configuration</label>
            <div class="vlan-config-grid">
              <select v-model="newPort.encapsulation" class="select-sm">
                <option value="dot1q">802.1Q (dot1q)</option>
              </select>
              
              <input 
                v-model.number="newPort.vlan_id" 
                type="number"
                class="input-sm" 
                placeholder="VLAN ID (e.g., 10)"
              />
            </div>
          </div>

          <!-- Konfiguracija IP Adrese (za rutere, podinterfejse, SVI) -->
          <div v-if="canAssignIP()" class="ip-config">
            <label class="vlan-label">Layer 3 Configuration</label>
            <div class="ip-config-grid">
              <input 
                v-model="newPort.ip_address" 
                class="input-sm" 
                placeholder="IP Address (e.g., 192.168.1.1)"
              />
              <input 
                v-model="newPort.subnet_mask" 
                class="input-sm" 
                placeholder="Subnet Mask (e.g., 255.255.255.0)"
              />
            </div>
            <input 
              v-model="newPort.description" 
              class="input-sm" 
              style="margin-top: 8px;"
              placeholder="Description (optional)"
            />
          </div>

          <div class="row-actions">
            <button 
              @click="confirmPort" 
              class="btn-add-sm" 
              :disabled="!newPort.name"
            >
              {{ editingPortIndex !== null ? 'Update' : 'Add' }}
            </button>
            <button 
              v-if="editingPortIndex !== null" 
              @click="cancelEdit" 
              class="btn-cancel-sm"
            >
              Cancel
            </button>
          </div>
        </div>

      </div>

      <!-- Tab Podmreža -->
      <div v-show="activeTab === 'subnets'" class="tab-content">
        
        <div class="subnet-list">
          <div v-for="(subnet, index) in localSubnets" :key="index" class="subnet-item">
            <div class="subnet-header">
              <span class="subnet-name">{{ subnet.network }}</span>
              <div class="subnet-actions">
                <button 
                  @click="editSubnet(index)" 
                  class="btn-icon-action" 
                  title="Edit Subnet"
                >
                  ✏️
                </button>
                <button 
                  @click="removeSubnet(index)" 
                  class="btn-icon-danger" 
                  title="Remove Subnet"
                >
                  🗑️
                </button>
              </div>
            </div>
            <div class="subnet-details">
              <span class="badge">{{ subnet.mask }}</span>
              <span class="badge ip">{{ subnet.gateway }}</span>
              <span v-if="subnet.vlan_id" class="badge vlan-id">VLAN {{ subnet.vlan_id }}</span>
              <span v-if="subnet.description" class="badge-desc">{{ subnet.description }}</span>
            </div>
          </div>
        </div>

        <!-- Sekcija za dodavanje/izmenu Podmreže -->
        <div :class="['add-port-section', { editing: editingSubnetIndex !== null }]">
          <h4>{{ editingSubnetIndex !== null ? '✏️ Edit' : '➕ Add' }} Subnet</h4>
          
          <div class="subnet-form">
            <input 
              v-model="newSubnet.network" 
              class="input-sm" 
              placeholder="Network (e.g., 192.168.10.0)"
            />
            
            <select v-model="newSubnet.mask" class="select-sm">
              <option value="255.255.255.0">/24 (255.255.255.0)</option>
              <option value="255.255.255.128">/25 (255.255.255.128)</option>
              <option value="255.255.255.192">/26 (255.255.255.192)</option>
              <option value="255.255.255.224">/27 (255.255.255.224)</option>
              <option value="255.255.255.240">/28 (255.255.255.240)</option>
              <option value="255.255.255.248">/29 (255.255.255.248)</option>
              <option value="255.255.255.252">/30 (255.255.255.252)</option>
              <option value="255.255.254.0">/23 (255.255.254.0)</option>
              <option value="255.255.252.0">/22 (255.255.252.0)</option>
              <option value="255.255.248.0">/21 (255.255.248.0)</option>
              <option value="255.255.240.0">/20 (255.255.240.0)</option>
              <option value="255.255.0.0">/16 (255.255.0.0)</option>
            </select>
            
            <input 
              v-model="newSubnet.gateway" 
              class="input-sm" 
              placeholder="Gateway IP (e.g., 192.168.10.1)"
            />
            
            <input 
              v-model.number="newSubnet.vlan_id" 
              type="number"
              class="input-sm" 
              placeholder="VLAN ID (optional)"
            />
            
            <input 
              v-model="newSubnet.description" 
              class="input-sm" 
              placeholder="Description (optional)"
              style="grid-column: span 2;"
            />
          </div>

          <div class="row-actions">
            <button 
              @click="confirmSubnet" 
              class="btn-add-sm" 
              :disabled="!newSubnet.network || !newSubnet.gateway"
            >
              {{ editingSubnetIndex !== null ? 'Update' : 'Add' }}
            </button>
            <button 
              v-if="editingSubnetIndex !== null" 
              @click="cancelSubnetEdit" 
              class="btn-cancel-sm"
            >
              Cancel
            </button>
          </div>
        </div>

      </div>

      <!-- Tab VLAN-ova -->
      <div v-show="activeTab === 'vlans'" class="tab-content">
        
        <div class="vlan-list">
          <div v-for="(vlan, index) in localVlans" :key="index" class="vlan-item">
            <div class="vlan-header">
              <span class="vlan-id">VLAN {{ vlan.vlan_id }}</span>
              <span class="vlan-name">{{ vlan.name }}</span>
              <div class="vlan-actions">
                <button 
                  @click="editVlan(index)" 
                  class="btn-icon-action" 
                  title="Edit VLAN"
                >
                  ✏️
                </button>
                <button 
                  @click="removeVlan(index)" 
                  class="btn-icon-danger" 
                  title="Remove VLAN"
                >
                  🗑️
                </button>
              </div>
            </div>
            <div class="vlan-details">
              <span :class="['badge', vlan.status === 'active' ? 'active' : 'suspended']">{{ vlan.status }}</span>
              <span v-if="vlan.description" class="vlan-description">{{ vlan.description }}</span>
            </div>
          </div>
        </div>

        <!-- Forma za dodavanje/izmenu VLAN-a -->
        <div class="add-vlan-section">
          <h4>{{ editingVlanIndex !== null ? '✏️ Edit VLAN' : '➕ Add VLAN' }}</h4>
          
          <div class="vlan-form-grid">
            <label class="form-label">VLAN ID *</label>
            <input 
              v-model.number="newVlan.vlan_id" 
              type="number"
              min="1"
              max="4094"
              class="input-sm" 
              placeholder="e.g., 10"
            />
            
            <label class="form-label">VLAN Name *</label>
            <input 
              v-model="newVlan.name" 
              type="text"
              class="input-sm" 
              placeholder="e.g., Management"
            />
            
            <label class="form-label">Status</label>
            <select v-model="newVlan.status" class="input-sm">
              <option value="active">Active</option>
              <option value="suspended">Suspended</option>
            </select>
            
            <label class="form-label">Description</label>
            <input 
              v-model="newVlan.description" 
              type="text"
              class="input-sm" 
              placeholder="Optional description"
            />
          </div>

          <div class="vlan-form-actions">
            <button 
              @click="confirmVlan" 
              class="btn-confirm-sm"
              :disabled="!newVlan.vlan_id || !newVlan.name"
            >
              {{ editingVlanIndex !== null ? 'Update VLAN' : 'Add VLAN' }}
            </button>
            <button 
              v-if="editingVlanIndex !== null" 
              @click="cancelVlanEdit" 
              class="btn-cancel-sm"
            >
              Cancel
            </button>
          </div>
        </div>

      </div>

      <!-- Tab Statičkih Ruta -->
      <div v-show="activeTab === 'routes'" class="tab-content">
        
        <div class="route-list">
          <div v-for="(route, index) in localRoutes" :key="index" class="route-item">
            <div class="route-header">
              <span class="route-network">{{ route.destination_network }}/{{ cidrFromMask(route.subnet_mask) }}</span>
              <div class="route-actions">
                <button 
                  @click="editRoute(index)" 
                  class="btn-icon-action" 
                  title="Edit Route"
                >
                  ✏️
                </button>
                <button 
                  @click="removeRoute(index)" 
                  class="btn-icon-danger" 
                  title="Remove Route"
                >
                  🗑️
                </button>
              </div>
            </div>
            <div class="route-details">
              <span v-if="route.next_hop" class="badge ip">via {{ route.next_hop }}</span>
              <span v-if="route.exit_interface" class="badge">{{ route.exit_interface }}</span>
              <span class="badge">AD: {{ route.metric || 1 }}</span>
              <span v-if="isDefaultRoute(route)" class="badge default-route">Default Route</span>
              <span v-if="route.description" class="badge-desc">{{ route.description }}</span>
            </div>
          </div>
        </div>

        <!-- Sekcija za dodavanje/izmenu Rute -->
        <div :class="['add-port-section', { editing: editingRouteIndex !== null }]">
          <h4>{{ editingRouteIndex !== null ? '✏️ Edit' : '➕ Add' }} Static Route</h4>
          
          <div class="route-form">
            <label class="form-label">Destination Network *</label>
            <input 
              v-model="newRoute.destination_network" 
              class="input-sm" 
              placeholder="e.g., 192.168.20.0 or 0.0.0.0"
            />
            
            <label class="form-label">Subnet Mask *</label>
            <select v-model="newRoute.subnet_mask" class="select-sm">
              <option value="0.0.0.0">Default Route (0.0.0.0)</option>
              <option value="255.255.255.252">/30 (255.255.255.252)</option>
              <option value="255.255.255.248">/29 (255.255.255.248)</option>
              <option value="255.255.255.240">/28 (255.255.255.240)</option>
              <option value="255.255.255.224">/27 (255.255.255.224)</option>
              <option value="255.255.255.192">/26 (255.255.255.192)</option>
              <option value="255.255.255.128">/25 (255.255.255.128)</option>
              <option value="255.255.255.0">/24 (255.255.255.0)</option>
              <option value="255.255.254.0">/23 (255.255.254.0)</option>
              <option value="255.255.252.0">/22 (255.255.252.0)</option>
              <option value="255.255.248.0">/21 (255.255.248.0)</option>
              <option value="255.255.240.0">/20 (255.255.240.0)</option>
              <option value="255.255.0.0">/16 (255.255.0.0)</option>
              <option value="255.0.0.0">/8 (255.0.0.0)</option>
            </select>
            
            <label class="form-label">Next-Hop IP</label>
            <input 
              v-model="newRoute.next_hop" 
              class="input-sm" 
              placeholder="e.g., 10.0.0.2 (optional if exit interface)"
            />
            
            <label class="form-label">Exit Interface</label>
            <select v-model="newRoute.exit_interface" class="select-sm">
              <option value="">-- None --</option>
              <option v-for="port in availablePorts" :key="port.name" :value="port.name">
                {{ port.name }}
              </option>
            </select>
            
            <label class="form-label">Metric (AD)</label>
            <input 
              v-model.number="newRoute.metric" 
              type="number"
              min="1"
              max="255"
              class="input-sm" 
              placeholder="1"
            />
            
            <label class="form-label" style="grid-column: span 2;">Description (optional)</label>
            <input 
              v-model="newRoute.description" 
              class="input-sm" 
              placeholder="e.g., Route to remote network"
              style="grid-column: span 2;"
            />
          </div>

          <div class="row-actions">
            <button 
              @click="confirmRoute" 
              class="btn-add-sm" 
              :disabled="!newRoute.destination_network || !newRoute.subnet_mask || (!newRoute.next_hop && !newRoute.exit_interface)"
            >
              {{ editingRouteIndex !== null ? 'Update' : 'Add' }}
            </button>
            <button 
              v-if="editingRouteIndex !== null" 
              @click="cancelRouteEdit" 
              class="btn-cancel-sm"
            >
              Cancel
            </button>
          </div>
          
          <div class="route-help">
            💡 <strong>Tip:</strong> For default route, use 0.0.0.0/0.0.0.0. Must specify either next-hop IP or exit interface (or both).
          </div>
        </div>

      </div>

      <!-- Path Analysis Tab -->
      <div v-show="activeTab === 'paths'" class="tab-content">
        <div class="paths-section">
          <h4>🛣️ Find Path to Device</h4>
          <p class="paths-help">Select a destination device to analyze all possible network paths.</p>
          
          <div class="target-selector">
            <label class="form-label">Destination Device</label>
            <select v-model="selectedTargetKey" class="input-sm">
              <option value="">-- Select Device --</option>
              <option 
                v-for="device in availableDevices" 
                :key="device.key" 
                :value="device.key"
              >
                {{ device.hostname }} ({{ device.device_type }})
              </option>
            </select>
            <button 
              type="button"
              @click="analyzePaths" 
              :disabled="!selectedTargetKey || analyzingPaths"
              class="btn-analyze"
            >
              {{ analyzingPaths ? '⏳ Analyzing...' : '🔍 Analyze Paths' }}
            </button>
            <button 
              type="button"
              @click="clearHighlights" 
              class="btn-clear"
              title="Clear highlighted paths on canvas"
              style="margin-left: 5px; padding: 6px 10px; background: #9e9e9e; color: white; border: none; border-radius: 4px; cursor: pointer;"
            >
              🧹 Clear
            </button>
          </div>

          <!-- Debug Info -->
          <div v-if="pathResults" style="background: #f0f0f0; padding: 10px; margin: 10px 0; font-size: 11px;">
            <strong>Debug:</strong> Total paths: {{ pathResults.total_paths_found }}<br>
            Has shortest: {{ !!pathResults.shortest_path }}<br>
            Has cheapest: {{ !!pathResults.cheapest_path }}<br>
            Alt paths: {{ pathResults.alternative_paths?.length || 0 }}
          </div>

          <!-- Path Results -->
          <div v-if="pathResults" class="path-results">
            <div class="path-summary">
              <strong>From:</strong> {{ pathResults.source.hostname }} 
              <strong>To:</strong> {{ pathResults.target.hostname }}
              <span class="paths-found">{{ pathResults.total_paths_found }} paths found</span>
            </div>

            <!-- Shortest Path (Green) -->
            <div v-if="pathResults.shortest_path" class="path-card shortest">
              <div class="path-header">
                <span class="path-badge green">🟢 Shortest Path</span>
                <span class="path-hops">{{ pathResults.shortest_path.hops }} hops</span>
              </div>
              <div class="path-devices">
                <span 
                  v-for="(device, idx) in pathResults.shortest_path.devices" 
                  :key="idx"
                  class="path-device-name"
                >
                  {{ device.hostname }}{{ idx < pathResults.shortest_path.devices.length - 1 ? ' → ' : '' }}
                </span>
              </div>
              <div class="path-cost">Cost: {{ pathResults.shortest_path.cost }} (avg: {{ pathResults.shortest_path.avg_cost }})</div>
              
              <details class="path-details">
                <summary>📋 View Connection Details</summary>
                <div class="connection-list">
                  <div v-for="(conn, idx) in pathResults.shortest_path.connections" :key="idx" class="connection-item">
                    <div class="conn-header">Hop {{ idx + 1 }}: {{ conn.from }} → {{ conn.to }}</div>
                    <div class="conn-info">
                      <span class="conn-label">Cable:</span> {{ conn.cable_type }} @ {{ conn.speed }}
                    </div>
                  </div>
                </div>
              </details>
              
              <button @click="highlightPath(pathResults.shortest_path, 'green')" class="btn-highlight">
                🎨 Highlight on Canvas
              </button>
            </div>

            <!-- Cheapest Path (Red) -->
            <div v-if="pathResults.cheapest_path && pathResults.cheapest_path !== pathResults.shortest_path" class="path-card cheapest">
              <div class="path-header">
                <span class="path-badge red">🔴 Cheapest Path</span>
                <span class="path-hops">{{ pathResults.cheapest_path.hops }} hops</span>
              </div>
              <div class="path-devices">
                <span 
                  v-for="(device, idx) in pathResults.cheapest_path.devices" 
                  :key="idx"
                  class="path-device-name"
                >
                  {{ device.hostname }}{{ idx < pathResults.cheapest_path.devices.length - 1 ? ' → ' : '' }}
                </span>
              </div>
              <div class="path-cost">Cost: {{ pathResults.cheapest_path.cost }} (avg: {{ pathResults.cheapest_path.avg_cost }})</div>
              
              <details class="path-details">
                <summary>📋 View Connection Details</summary>
                <div class="connection-list">
                  <div v-for="(conn, idx) in pathResults.cheapest_path.connections" :key="idx" class="connection-item">
                    <div class="conn-header">Hop {{ idx + 1 }}: {{ conn.from }} → {{ conn.to }}</div>
                    <div class="conn-info">
                      <span class="conn-label">Cable:</span> {{ conn.cable_type }} @ {{ conn.speed }}
                    </div>
                  </div>
                </div>
              </details>
              
              <button @click="highlightPath(pathResults.cheapest_path, 'red')" class="btn-highlight">
                🎨 Highlight on Canvas
              </button>
            </div>

            <!-- Alternative Paths (Yellow) -->
            <div v-if="pathResults.alternative_paths && pathResults.alternative_paths.length > 0">
              <h5 class="alt-paths-title">Alternative Paths</h5>
              <div 
                v-for="(path, idx) in pathResults.alternative_paths" 
                :key="idx"
                class="path-card alternative"
              >
                <div class="path-header">
                  <span class="path-badge yellow">🟡 Alternative {{ idx + 1 }}</span>
                  <span class="path-hops">{{ path.hops }} hops</span>
                </div>
                <div class="path-devices">
                  <span 
                    v-for="(device, dIdx) in path.devices" 
                    :key="dIdx"
                    class="path-device-name"
                  >
                    {{ device.hostname }}{{ dIdx < path.devices.length - 1 ? ' → ' : '' }}
                  </span>
                </div>
                <div class="path-cost">Cost: {{ path.cost }} (avg: {{ path.avg_cost }})</div>
                
                <details class="path-details">
                  <summary>📋 View Connection Details</summary>
                  <div class="connection-list">
                    <div v-for="(conn, cIdx) in path.connections" :key="cIdx" class="connection-item">
                      <div class="conn-header">Hop {{ cIdx + 1 }}: {{ conn.from }} → {{ conn.to }}</div>
                      <div class="conn-info">
                        <span class="conn-label">Cable:</span> {{ conn.cable_type }} @ {{ conn.speed }}
                      </div>
                    </div>
                  </div>
                </details>
                
                <button @click="highlightPath(path, 'yellow')" class="btn-highlight">
                  🎨 Highlight on Canvas
                </button>
              </div>
            </div>

            <button @click="clearHighlights" class="btn-clear-highlights">
              ✕ Clear All Highlights
            </button>
          </div>

          <div v-else-if="!selectedTargetKey" class="no-paths">
            Select a destination device to begin path analysis
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="panel-footer">
      <button @click="saveChanges" class="btn btn-success">
        💾 Save Changes
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { analyzePathsAPI } from '../services/api.js'

const props = defineProps({
  node: Object,
  canvas: Object
})

const emit = defineEmits(['update', 'close', 'highlight-path', 'clear-highlights'])

const activeTab = ref('general')
const localPorts = ref([])
const localSubnets = ref([])
const localRoutes = ref([])
const localVlans = ref([])
const editingPortIndex = ref(null)
const editingSubnetIndex = ref(null)
const editingRouteIndex = ref(null)
const editingVlanIndex = ref(null)

// Path analysis state
const selectedTargetKey = ref('')
const pathResults = ref(null)
const analyzingPaths = ref(false)
const showingSubinterfaceForm = ref(false)
const subinterfaceParent = ref('')

const newPort = reactive({
  name: '',
  type: 'ethernet',
  speed: '1Gbps',
  mode: null,
  vlan: '',
  encapsulation: 'dot1q',
  vlan_id: null,
  is_svi: false,
  is_routed: false,
  ip_address: '',
  subnet_mask: '',
  description: ''
})

const formData = ref({
  hostname: '',
  mac_address: '',
  router_id: '',
  color: '#eef2f5'
})

const subinterfaceName = computed(() => {
  if (subinterfaceParent.value && newSubinterface.vlan_id) {
    return `${subinterfaceParent.value}.${newSubinterface.vlan_id}`
  }
  return ''
})

const newSubnet = reactive({
  network: '',
  mask: '255.255.255.0',
  gateway: '',
  vlan_id: null,
  description: ''
})

const newSubinterface = reactive({
  vlan_id: null,
  ip_address: '',
  subnet_mask: '255.255.255.0',
  description: '',
  encapsulation: 'dot1q'
})

const newRoute = reactive({
  destination_network: '',
  subnet_mask: '255.255.255.0',
  next_hop: '',
  exit_interface: '',
  metric: 1,
  description: ''
})

const newVlan = reactive({
  vlan_id: null,
  name: '',
  status: 'active',
  description: ''
})

const availablePorts = computed(() => {
  return localPorts.value.filter(p => !p.is_svi)
})

function getIcon(type) {
  const icons = {
    router: '🔷',
    switch: '🔶',
    l3_switch: '🔷',
    server: '🖥️',
    client: '💻',
    zone: '🔲' 
  }
  return icons[type] || '?'
}

function shortSpeed(val) {
  if (!val) return ''
  return val.replace('Gbps', 'G').replace('Mbps', 'M')
}

function isSubinterface(portName) {
  // Check if port name contains a dot (e.g., Gi0/0.10)
  return portName && portName.includes('.')
}

function isEndDevice() {
  const deviceType = props.node.data.device_type
  return ['client', 'server', 'pc'].includes(deviceType)
}

function canAssignIP() {
  const deviceType = props.node.data.device_type
  
  // Routers: can assign IP on physical ports or subinterfaces
  if (deviceType === 'router') {
    return true
  }
  
  // L2 Switches: can only assign IP on SVIs
  if (deviceType === 'switch' && newPort.is_svi) {
    return true
  }
  
  // L3 Switches: can assign IP on SVIs or routed ports
  if (deviceType === 'l3_switch') {
    return true
  }
  
  // End devices (client, server, pc): can assign IP on NICs
  if (isEndDevice()) {
    return true
  }
  
  return false
}

function createSVI() {
  const vlanId = prompt('Create SVI (Switch Virtual Interface)\n\nEnter VLAN ID (e.g., 10):', '10')
  
  if (vlanId && !isNaN(vlanId)) {
    // Pre-fill the form with SVI data
    newPort.name = `vlan${vlanId}`
    newPort.type = 'svi'
    newPort.speed = 'N/A'
    newPort.is_svi = true
    newPort.vlan_id = parseInt(vlanId)
    newPort.mode = null
    newPort.vlan = ''
    newPort.encapsulation = ''
    
    // Auto-confirm to add it directly
    confirmPort()
  }
}

function createLoopback() {
  // Find highest loopback number
  const loopbackPorts = localPorts.value.filter(p => p.type === 'loopback' || p.name.toLowerCase().startsWith('loopback'))
  let nextNum = 0
  
  if (loopbackPorts.length > 0) {
    const numbers = loopbackPorts.map(p => {
      const match = p.name.match(/\d+/)
      return match ? parseInt(match[0]) : 0
    })
    nextNum = Math.max(...numbers) + 1
  }
  
  const loopbackName = prompt(`Create Loopback Interface\n\nEnter loopback number:`, nextNum.toString())
  
  if (loopbackName !== null) {
    const num = loopbackName || nextNum
    
    // Pre-fill the form with loopback data
    newPort.name = `Loopback${num}`
    newPort.type = 'loopback'
    newPort.speed = 'N/A'
    newPort.is_svi = false
    newPort.is_routed = false
    newPort.mode = null
    newPort.vlan = ''
    newPort.vlan_id = null
    newPort.encapsulation = ''
    
    // Auto-confirm to add it directly
    confirmPort()
  }
}

function cidrFromMask(mask) {
  const maskMap = {
    '0.0.0.0': '0',
    '128.0.0.0': '1',
    '192.0.0.0': '2',
    '224.0.0.0': '3',
    '240.0.0.0': '4',
    '248.0.0.0': '5',
    '252.0.0.0': '6',
    '254.0.0.0': '7',
    '255.0.0.0': '8',
    '255.128.0.0': '9',
    '255.192.0.0': '10',
    '255.224.0.0': '11',
    '255.240.0.0': '12',
    '255.248.0.0': '13',
    '255.252.0.0': '14',
    '255.254.0.0': '15',
    '255.255.0.0': '16',
    '255.255.128.0': '17',
    '255.255.192.0': '18',
    '255.255.224.0': '19',
    '255.255.240.0': '20',
    '255.255.248.0': '21',
    '255.255.252.0': '22',
    '255.255.254.0': '23',
    '255.255.255.0': '24',
    '255.255.255.128': '25',
    '255.255.255.192': '26',
    '255.255.255.224': '27',
    '255.255.255.240': '28',
    '255.255.255.248': '29',
    '255.255.255.252': '30',
    '255.255.255.254': '31',
    '255.255.255.255': '32'
  }
  return maskMap[mask] || '?'
}

function isDefaultRoute(route) {
  return route.destination_network === '0.0.0.0' && route.subnet_mask === '0.0.0.0'
}

function editRoute(index) {
  const route = localRoutes.value[index]
  newRoute.destination_network = route.destination_network
  newRoute.subnet_mask = route.subnet_mask
  newRoute.next_hop = route.next_hop || ''
  newRoute.exit_interface = route.exit_interface || ''
  newRoute.metric = route.metric || 1
  newRoute.description = route.description || ''
  editingRouteIndex.value = index
}

function removeRoute(index) {
  if (confirm('Remove this static route?')) {
    localRoutes.value.splice(index, 1)
  }
}

function confirmRoute() {
  if (!newRoute.destination_network || !newRoute.subnet_mask) return
  if (!newRoute.next_hop && !newRoute.exit_interface) return

  const routeData = {
    destination_network: newRoute.destination_network,
    subnet_mask: newRoute.subnet_mask,
    metric: newRoute.metric || 1
  }

  if (newRoute.next_hop) {
    routeData.next_hop = newRoute.next_hop
  }

  if (newRoute.exit_interface) {
    routeData.exit_interface = newRoute.exit_interface
  }

  if (newRoute.description) {
    routeData.description = newRoute.description
  }

  if (editingRouteIndex.value !== null) {
    localRoutes.value[editingRouteIndex.value] = routeData
    editingRouteIndex.value = null
  } else {
    localRoutes.value.push(routeData)
  }

  // Reset form
  newRoute.destination_network = ''
  newRoute.subnet_mask = '255.255.255.0'
  newRoute.next_hop = ''
  newRoute.exit_interface = ''
  newRoute.metric = 1
  newRoute.description = ''
}

function cancelRouteEdit() {
  editingRouteIndex.value = null
  newRoute.destination_network = ''
  newRoute.subnet_mask = '255.255.255.0'
  newRoute.next_hop = ''
  newRoute.exit_interface = ''
  newRoute.metric = 1
  newRoute.description = ''
}

// VLAN management functions
function editVlan(index) {
  const vlan = localVlans.value[index]
  newVlan.vlan_id = vlan.vlan_id
  newVlan.name = vlan.name
  newVlan.status = vlan.status
  newVlan.description = vlan.description || ''
  editingVlanIndex.value = index
}

function removeVlan(index) {
  if (confirm('Remove this VLAN?')) {
    localVlans.value.splice(index, 1)
  }
}

function confirmVlan() {
  if (!newVlan.vlan_id || !newVlan.name) return

  const vlanData = {
    vlan_id: newVlan.vlan_id,
    name: newVlan.name,
    status: newVlan.status
  }

  if (newVlan.description) {
    vlanData.description = newVlan.description
  }

  if (editingVlanIndex.value !== null) {
    localVlans.value[editingVlanIndex.value] = vlanData
    editingVlanIndex.value = null
  } else {
    // Check for duplicate VLAN ID
    const exists = localVlans.value.find(v => v.vlan_id === newVlan.vlan_id)
    if (exists) {
      alert(`VLAN ${newVlan.vlan_id} already exists!`)
      return
    }
    localVlans.value.push(vlanData)
  }

  // Reset form
  newVlan.vlan_id = null
  newVlan.name = ''
  newVlan.status = 'active'
  newVlan.description = ''
}

function cancelVlanEdit() {
  editingVlanIndex.value = null
  newVlan.vlan_id = null
  newVlan.name = ''
  newVlan.status = 'active'
  newVlan.description = ''
}

watch(() => props.node, (newNode) => {
  if (newNode) {
    formData.value = {
      hostname: newNode.data.hostname,
      mac_address: newNode.data.mac_address,
      router_id: newNode.data.router_id || '',
      color: newNode.data.color || '#eef2f5'
    }
    
    localPorts.value = newNode.data.ports ? JSON.parse(JSON.stringify(newNode.data.ports)) : []
    localSubnets.value = newNode.data.subnets ? JSON.parse(JSON.stringify(newNode.data.subnets)) : []
    localVlans.value = newNode.data.vlans ? JSON.parse(JSON.stringify(newNode.data.vlans)) : []
    localRoutes.value = newNode.data.static_routes ? JSON.parse(JSON.stringify(newNode.data.static_routes)) : []
  }
}, { immediate: true })

function editSubnet(index) {
  const subnet = localSubnets.value[index]
  newSubnet.network = subnet.network
  newSubnet.mask = subnet.mask
  newSubnet.gateway = subnet.gateway
  newSubnet.vlan_id = subnet.vlan_id || null
  newSubnet.description = subnet.description || ''
  editingSubnetIndex.value = index
}

function removeSubnet(index) {
  if (confirm('Remove this subnet?')) {
    localSubnets.value.splice(index, 1)
  }
}

function confirmSubnet() {
  if (!newSubnet.network || !newSubnet.gateway) return

  const subnetData = {
    network: newSubnet.network,
    mask: newSubnet.mask,
    gateway: newSubnet.gateway
  }

  if (newSubnet.vlan_id) {
    subnetData.vlan_id = newSubnet.vlan_id
  }

  if (newSubnet.description) {
    subnetData.description = newSubnet.description
  }

  if (editingSubnetIndex.value !== null) {
    localSubnets.value[editingSubnetIndex.value] = subnetData
    editingSubnetIndex.value = null
  } else {
    localSubnets.value.push(subnetData)
  }

  // Reset form
  newSubnet.network = ''
  newSubnet.mask = '255.255.255.0'
  newSubnet.gateway = ''
  newSubnet.vlan_id = null
  newSubnet.description = ''
}

function cancelSubnetEdit() {
  editingSubnetIndex.value = null
  newSubnet.network = ''
  newSubnet.mask = '255.255.255.0'
  newSubnet.gateway = ''
  newSubnet.vlan_id = null
  newSubnet.description = ''
}

function showSubinterfaceForm(parentPort) {
  subinterfaceParent.value = parentPort
  showingSubinterfaceForm.value = true
  newSubinterface.vlan_id = null
  newSubinterface.ip_address = ''
  newSubinterface.subnet_mask = '255.255.255.0'
  newSubinterface.description = ''
  newSubinterface.encapsulation = 'dot1q'
}

function createSubinterface() {
  if (!newSubinterface.vlan_id || !newSubinterface.ip_address) return
  
  const subinterfaceName = `${subinterfaceParent.value}.${newSubinterface.vlan_id}`
  
  const portData = {
    name: subinterfaceName,
    type: 'ethernet',
    speed: '1Gbps',
    encapsulation: newSubinterface.encapsulation,
    vlan_id: newSubinterface.vlan_id,
    ip_address: newSubinterface.ip_address,
    subnet_mask: newSubinterface.subnet_mask
  }
  
  if (newSubinterface.description) {
    portData.description = newSubinterface.description
  }
  
  localPorts.value.push(portData)
  cancelSubinterfaceForm()
}

function cancelSubinterfaceForm() {
  showingSubinterfaceForm.value = false
  subinterfaceParent.value = ''
  newSubinterface.vlan_id = null
  newSubinterface.ip_address = ''
  newSubinterface.subnet_mask = '255.255.255.0'
  newSubinterface.description = ''
  newSubinterface.encapsulation = 'dot1q'
}

function editPort(index) {
  const port = localPorts.value[index]
  newPort.name = port.name
  newPort.type = port.type
  newPort.speed = port.speed
  newPort.mode = port.mode || null
  newPort.vlan = port.vlan || ''
  newPort.encapsulation = port.encapsulation || 'dot1q'
  newPort.vlan_id = port.vlan_id || null
  newPort.is_svi = port.is_svi || false
  newPort.is_routed = port.is_routed || false
  newPort.ip_address = port.ip_address || ''
  newPort.subnet_mask = port.subnet_mask || ''
  newPort.description = port.description || ''
  editingPortIndex.value = index
}

function removePort(index) {
  if (confirm('Remove this port?')) {
    localPorts.value.splice(index, 1)
  }
}

function confirmPort() {
  if (!newPort.name) return

  const portData = {
    name: newPort.name,
    type: newPort.type,
    speed: newPort.speed,
    is_svi: newPort.is_svi,
    is_routed: newPort.is_routed
  }

  // Add VLAN config for switches (L2 configuration)
  if (props.node.data.device_type === 'switch' && newPort.mode) {
    portData.mode = newPort.mode
    portData.vlan = newPort.vlan
  }

  // Add L3 switch port config (routed or switchport)
  if (props.node.data.device_type === 'l3_switch' && !newPort.is_svi) {
    if (newPort.is_routed) {
      // Routed port - no switchport mode
      portData.is_routed = true
    } else {
      // Switchport mode
      portData.is_routed = false
      if (newPort.mode) {
        portData.mode = newPort.mode
        portData.vlan = newPort.vlan
      }
    }
  }

  // Add subinterface config for routers
  if (props.node.data.device_type === 'router' && isSubinterface(newPort.name)) {
    portData.encapsulation = newPort.encapsulation
    portData.vlan_id = newPort.vlan_id
  }

  // Add SVI VLAN ID for switches
  if (newPort.is_svi && newPort.vlan_id) {
    portData.vlan_id = newPort.vlan_id
  }

  // Add IP configuration if provided
  if (newPort.ip_address) {
    portData.ip_address = newPort.ip_address
    portData.subnet_mask = newPort.subnet_mask || '255.255.255.0'
  }

  if (newPort.description) {
    portData.description = newPort.description
  }

  if (editingPortIndex.value !== null) {
    localPorts.value[editingPortIndex.value] = portData
    editingPortIndex.value = null
  } else {
    localPorts.value.push(portData)
  }

  // Reset form
  newPort.name = ''
  newPort.type = 'ethernet'
  newPort.speed = '1Gbps'
  newPort.mode = null
  newPort.vlan = ''
  newPort.encapsulation = 'dot1q'
  newPort.vlan_id = null
  newPort.is_svi = false
  newPort.is_routed = false
  newPort.ip_address = ''
  newPort.subnet_mask = ''
  newPort.description = ''
}

function cancelEdit() {
  editingPortIndex.value = null
  newPort.name = ''
  newPort.type = 'ethernet'
  newPort.speed = '1Gbps'
  newPort.mode = null
  newPort.vlan = ''
  newPort.encapsulation = 'dot1q'
  newPort.vlan_id = null
  newPort.is_svi = false
  newPort.is_routed = false
  newPort.ip_address = ''
  newPort.subnet_mask = ''
  newPort.description = ''
}

function onColorChange() {
  if (props.node.data.device_type === 'zone') {
    emit('update', props.node.id, { color: formData.value.color }, true)
  }
}

// Computed property for available devices (excluding current device)
const availableDevices = computed(() => {
  if (!props.canvas || !props.canvas.getNodes) {
    return []
  }
  
  const allNodes = props.canvas.getNodes() || []
  const currentKey = props.node.data._key || props.node.data.key
  
  return allNodes
    .filter(n => n.data.device_type !== 'zone' && n.data._key !== currentKey)
    .map(n => ({
      key: n.data._key,
      hostname: n.data.hostname,
      device_type: n.data.device_type
    }))
})

// Path analysis functions
async function analyzePaths() {
  if (!selectedTargetKey.value) return
  
  analyzingPaths.value = true
  pathResults.value = null
  
  try {
    const sourceKey = props.node.data._key || props.node.data.key || props.node.id
    const targetKey = selectedTargetKey.value
    
    console.log('Analyzing paths from', sourceKey, 'to', targetKey)
    console.log('Source node data:', props.node.data)
    
    const response = await analyzePathsAPI(sourceKey, targetKey)
    console.log('Full response:', response)
    console.log('Response data:', response.data)
    
    if (!response.data) {
      throw new Error('No data in response')
    }
    
    pathResults.value = response.data
    
    if (pathResults.value && pathResults.value.total_paths_found === 0) {
      alert('No paths found between these devices. Make sure:\n1. You clicked Save to persist the topology\n2. The devices are connected\n3. The connections form a valid path')
    }
  } catch (error) {
    console.error('Failed to analyze paths:', error)
    const errorMsg = error.response?.data?.detail || error.message
    alert('Failed to analyze paths: ' + errorMsg + '\n\nTip: Make sure you saved the topology first!')
  } finally {
    analyzingPaths.value = false
  }
}

function highlightPath(path, color) {
  emit('highlight-path', { path, color })
}

function clearHighlights() {
  if (props.canvas) {
    props.canvas.clearPathHighlights()
  }
  pathResults.value = null
  selectedTargetKey.value = ''
  emit('clear-highlights')
}

function saveChanges() {
  const updates = {
    hostname: formData.value.hostname,
    mac_address: formData.value.mac_address,
    router_id: formData.value.router_id,
    ports: localPorts.value,
    subnets: localSubnets.value,
    vlans: localVlans.value,
    static_routes: localRoutes.value
  }

  if (props.node.data.device_type === 'zone') {
    updates.color = formData.value.color
  }

  emit('update', props.node.id, updates)
  emit('close')
}
</script>

<style scoped>
.properties-panel {
  position: fixed;
  right: 0;
  top: 60px;
  width: 400px;
  height: calc(100vh - 60px);
  background: white;
  box-shadow: -4px 0 15px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  z-index: 100;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #eee;
}

.panel-body {
  flex: 1;
  padding: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.device-preview-header {
  padding: 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  display: flex;
  justify-content: center;
}

.preview-node-mini {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 10px 20px;
  background: white;
  border-radius: 50px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.preview-icon {
  font-size: 24px;
}

.preview-details {
  display: flex;
  flex-direction: column;
}

.preview-hostname {
  font-weight: bold;
  font-size: 16px;
  color: #333;
}

.preview-type {
  font-size: 10px;
  text-transform: uppercase;
  color: #666;
  font-weight: 600;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #ddd;
}

.tab-btn {
  flex: 1;
  padding: 12px;
  background: none;
  border: none;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #f5f5f5;
  color: #333;
}

.tab-btn.active {
  color: #1976d2;
  border-bottom-color: #1976d2;
  background: rgba(25, 118, 210, 0.05);
}

.tab-content {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 600;
  color: #333;
  font-size: 13px;
}

.form-group .help-text {
  display: block;
  margin-top: 4px;
  font-size: 11px;
  color: #666;
  font-style: italic;
}

.form-group input, .form-group select, .form-group textarea {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

.port-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.port-item {
  background: #f8f9fa;
  border: 1px solid #eee;
  border-radius: 6px;
  padding: 10px;
}

.port-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.port-name {
  font-weight: bold;
  color: #333;
}

.port-actions {
  display: flex;
  gap: 5px;
}

.btn-icon-action, .btn-icon-danger {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.6;
}

.btn-icon-action:hover, .btn-icon-danger:hover {
  opacity: 1;
  transform: scale(1.1);
}

.port-details {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  background: #e0e0e0;
  color: #555;
  text-transform: uppercase;
}

.badge.fiber { background: #fff3e0; color: #f57c00; }
.badge.ethernet { background: #e3f2fd; color: #1565c0; }
.badge.svi { background: #e1f5fe; color: #01579b; font-weight: 600; }
.badge.loopback { background: #f3e5f5; color: #6a1b9a; font-weight: 600; }
.badge.routed { background: #e0f2f1; color: #00695c; font-weight: 600; }
.badge.speed { background: #f5f5f5; border: 1px solid #ddd; }
.badge.vlan-mode { background: #e8f5e9; color: #2e7d32; }
.badge.vlan-id { background: #fff9c4; color: #f57f17; }
.badge.subif { background: #fce4ec; color: #c2185b; }
.badge.ip { background: #e8eaf6; color: #3f51b5; font-family: monospace; }

.add-port-section {
  background: #f0f7ff;
  padding: 15px;
  border-radius: 8px;
  border: 1px dashed #1976d2;
}

.add-port-section h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #1565c0;
}

.add-port-grid {
  display: grid;
  grid-template-columns: 1.5fr 1fr 1fr;
  gap: 8px;
}

.input-sm, .select-sm {
  padding: 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 12px;
  width: 100%;
  box-sizing: border-box;
}

.row-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.btn-add-sm {
  flex: 1;
  background: #1976d2;
  color: white;
  border: none;
  padding: 8px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-add-sm:hover { background: #1565c0; }
.btn-add-sm:disabled { background: #ccc; cursor: not-allowed; }

.btn-cancel-sm {
  background: #f5f5f5;
  border: 1px solid #ddd;
  color: #333;
  padding: 8px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-cancel-sm:hover { background: #e0e0e0; }

.panel-footer {
  padding: 20px;
  border-top: 1px solid #ddd;
  background: white;
  margin-top: auto;
}

.btn {
  width: 100%;
  padding: 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-success {
  background: #4caf50;
  color: white;
}

.btn-success:hover {
  background: #45a049;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  color: #666;
}

.color-picker-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.color-input {
  width: 50px;
  height: 35px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.color-val {
  font-family: monospace;
  font-size: 12px;
  color: #666;
}

.vlan-config {
  margin-top: 12px;
  padding: 10px;
  background: #fafafa;
  border-radius: 4px;
  border: 1px solid #e0e0e0;
}

.vlan-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #555;
  margin-bottom: 8px;
}

.vlan-config-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 8px;
}

.ip-config {
  margin-top: 12px;
  padding: 10px;
  background: #f0f8ff;
  border-radius: 4px;
  border: 1px solid #b3d9ff;
}

.ip-config-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.subnet-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.subnet-item {
  background: #f0f8ff;
  border: 1px solid #b3d9ff;
  border-radius: 6px;
  padding: 10px;
}

.subnet-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.subnet-name {
  font-weight: bold;
  color: #1565c0;
  font-family: monospace;
}

.subnet-actions {
  display: flex;
  gap: 5px;
}

.subnet-details {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.badge-desc {
  font-size: 11px;
  color: #666;
  font-style: italic;
}

.subnet-form {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 10px;
}

.subinterface-form {
  background: #fff8e1;
  border: 1px dashed #ffa726;
}

.subinterface-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.form-label {
  font-size: 11px;
  font-weight: 600;
  color: #555;
  text-align: right;
  padding-right: 5px;
}

.route-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.route-item {
  background: #f0fff4;
  border: 1px solid #c6f6d5;
  border-radius: 6px;
  padding: 10px;
}

.route-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.route-network {
  font-weight: bold;
  color: #2d6a4f;
  font-family: monospace;
  font-size: 14px;
}

.route-actions {
  display: flex;
  gap: 5px;
}

.route-details {
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.route-form {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.route-help {
  background: #fff3cd;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
  color: #856404;
  margin-top: 10px;
}

.badge.default-route {
  background: #ffd700;
  color: #b8860b;
  font-weight: 700;
}

/* VLAN Styles */
.vlan-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.vlan-item {
  background: #e8f0fe;
  border: 1px solid #aecbfa;
  border-radius: 6px;
  padding: 10px;
}

.vlan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.vlan-id {
  font-weight: bold;
  color: #1967d2;
  font-family: monospace;
  font-size: 14px;
}

.vlan-name {
  font-weight: 600;
  color: #174ea6;
  margin-left: 10px;
}

.vlan-actions {
  display: flex;
  gap: 5px;
}

.vlan-details {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.vlan-description {
  color: #666;
  font-size: 12px;
  font-style: italic;
}

.vlan-form-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}

.vlan-form-actions {
  display: flex;
  gap: 8px;
}

.add-vlan-section {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border: 1px dashed #aecbfa;
}

.add-vlan-section h4 {
  margin: 0 0 15px 0;
  color: #1967d2;
  font-size: 14px;
  font-weight: 600;
}

.badge.active {
  background: #34a853;
  color: white;
}

.badge.suspended {
  background: #9aa0a6;
  color: white;
}

/* Path Analysis Styles */
.paths-section {
  padding: 10px;
}

.paths-help {
  color: #666;
  font-size: 13px;
  margin-bottom: 15px;
}

.target-selector {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 20px;
}

.btn-analyze {
  background: #1976d2;
  color: white;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
}

.btn-analyze:hover { background: #1565c0; }
.btn-analyze:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.path-results {
  margin-top: 20px;
}

.path-summary {
  background: #f0f4ff;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 15px;
  font-size: 13px;
}

.paths-found {
  float: right;
  background: #1976d2;
  color: white;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 600;
}

.path-card {
  background: white;
  border: 2px solid #ddd;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.path-card.shortest {
  border-color: #34a853;
  background: #f0fff4;
}

.path-card.cheapest {
  border-color: #ea4335;
  background: #fff5f5;
}

.path-card.alternative {
  border-color: #fbbc04;
  background: #fffbf0;
}

.path-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.path-badge {
  font-weight: 700;
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 12px;
}

.path-badge.green {
  background: #34a853;
  color: white;
}

.path-badge.red {
  background: #ea4335;
  color: white;
}

.path-badge.yellow {
  background: #fbbc04;
  color: #333;
}

.path-hops {
  font-size: 11px;
  color: #666;
  font-weight: 600;
  background: #f1f3f4;
  padding: 3px 8px;
  border-radius: 8px;
}

.path-devices {
  font-family: monospace;
  font-size: 11px;
  color: #333;
  margin-bottom: 8px;
  line-height: 1.6;
}

.path-device-name {
  font-weight: 600;
}

.path-cost {
  font-size: 11px;
  color: #666;
  margin-bottom: 8px;
}

.btn-highlight {
  background: #4285f4;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  width: 100%;
}

.btn-highlight:hover {
  background: #3367d6;
}

.alt-paths-title {
  font-size: 13px;
  color: #333;
  font-weight: 700;
  margin: 15px 0 10px 0;
}

.btn-clear-highlights {
  background: #f44336;
  color: white;
  border: none;
  padding: 10px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  width: 100%;
  margin-top: 15px;
}

.btn-clear-highlights:hover {
  background: #d32f2f;
}

.no-paths {
  text-align: center;
  color: #999;
  padding: 40px 20px;
  font-style: italic;
}

/* Path Details Expandable */
.path-details {
  margin: 10px 0;
  border-top: 1px solid #e0e0e0;
  padding-top: 10px;
}

.path-details summary {
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  color: #1976d2;
  padding: 5px 0;
  user-select: none;
}

.path-details summary:hover {
  color: #1565c0;
}

.connection-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.connection-item {
  background: #f8f9fa;
  border-left: 3px solid #1976d2;
  padding: 8px;
  border-radius: 4px;
  font-size: 11px;
}

.conn-header {
  font-weight: 700;
  color: #333;
  margin-bottom: 4px;
  font-family: monospace;
}

.conn-info {
  color: #666;
  display: flex;
  gap: 5px;
  flex-wrap: wrap;
}

.conn-label {
  font-weight: 600;
  color: #555;
}
</style>

