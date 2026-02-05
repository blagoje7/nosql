# ArangoDB Schema Design - NetGraph Provisioner

## Database Configuration

```javascript
// Database: netgraph_db
// Graph: network_topology
// Vertex Collection: devices
// Edge Collection: connections
```

---

## 1. Vertex Collection: `devices`

### Document Structure

```json
{
  "_key": "router_r1",
  "_id": "devices/router_r1",
  "_rev": "_gXX1234",
  
  "hostname": "R1",
  "device_type": "router",
  "ip_address": "192.168.1.1",
  "mac_address": "00:1A:2B:3C:4D:5E",
  "subnet_mask": "255.255.255.0",
  "management_ip": "10.0.0.1",
  
  "hardware": {
    "vendor": "Cisco",
    "model": "ISR 4331",
    "serial_number": "FCZ1234A5B6"
  },
  
  "ports": [
    {
      "name": "eth0",
      "type": "ethernet",
      "speed": "1Gbps",
      "status": "up"
    },
    {
      "name": "eth1",
      "type": "ethernet",
      "speed": "10Gbps",
      "status": "up"
    }
  ],
  
  "metadata": {
    "location": "Datacenter A - Rack 3",
    "environment": "production",
    "created_at": "2026-01-19T10:30:00Z",
    "updated_at": "2026-01-19T10:30:00Z"
  },
  
  "ui_position": {
    "x": 250,
    "y": 150
  }
}
```

### Device Types & Examples

#### 1. Router
```json
{
  "_key": "router_core1",
  "hostname": "CORE-R1",
  "device_type": "router",
  "ip_address": "10.0.0.1",
  "mac_address": "00:1A:2B:3C:4D:5E",
  "subnet_mask": "255.255.255.0",
  "gateway": null,
  "routing_protocol": "OSPF",
  "ports": [
    {"name": "eth0", "type": "ethernet", "speed": "10Gbps"},
    {"name": "eth1", "type": "ethernet", "speed": "10Gbps"}
  ],
  "metadata": {
    "location": "Core Layer",
    "environment": "production"
  }
}
```

#### 2. Switch
```json
{
  "_key": "switch_sw1",
  "hostname": "SW1",
  "device_type": "switch",
  "ip_address": "192.168.1.10",
  "mac_address": "00:1A:2B:3C:4D:60",
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "vlan_support": true,
  "vlans": [10, 20, 30],
  "ports": [
    {"name": "port1", "type": "ethernet", "speed": "1Gbps"},
    {"name": "port2", "type": "ethernet", "speed": "1Gbps"},
    {"name": "port3", "type": "ethernet", "speed": "1Gbps"},
    {"name": "port4", "type": "fiber", "speed": "10Gbps"}
  ],
  "metadata": {
    "location": "Distribution Layer",
    "environment": "production"
  }
}
```

#### 3. Server
```json
{
  "_key": "server_web1",
  "hostname": "WEB-SERVER-1",
  "device_type": "server",
  "ip_address": "192.168.10.50",
  "mac_address": "00:1A:2B:3C:4D:70",
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.10.1",
  "os": "Ubuntu 22.04 LTS",
  "services": ["nginx", "postgresql"],
  "ports": [
    {"name": "eth0", "type": "ethernet", "speed": "1Gbps"}
  ],
  "metadata": {
    "location": "Access Layer",
    "environment": "production",
    "role": "web-server"
  }
}
```

---

## 2. Edge Collection: `connections`

### Document Structure

```json
{
  "_key": "conn_r1_sw1",
  "_id": "connections/conn_r1_sw1",
  "_from": "devices/router_r1",
  "_to": "devices/switch_sw1",
  "_rev": "_gYY5678",
  
  "src_port": "eth0",
  "dst_port": "port4",
  
  "cable_type": "fiber",
  "bandwidth": "10Gbps",
  "latency_ms": 0.5,
  "status": "active",
  
  "vlan_tags": [10, 20],
  
  "metadata": {
    "installed_date": "2026-01-10",
    "cable_length_meters": 15,
    "notes": "Direct fiber connection"
  }
}
```

### Connection Examples

#### 1. Router ↔ Switch (Uplink)
```json
{
  "_key": "conn_core1_sw1",
  "_from": "devices/router_core1",
  "_to": "devices/switch_sw1",
  "src_port": "eth0",
  "dst_port": "port4",
  "cable_type": "fiber",
  "bandwidth": "10Gbps",
  "status": "active",
  "vlan_tags": [10, 20, 30]
}
```

#### 2. Switch ↔ Server (Access)
```json
{
  "_key": "conn_sw1_web1",
  "_from": "devices/switch_sw1",
  "_to": "devices/server_web1",
  "src_port": "port1",
  "dst_port": "eth0",
  "cable_type": "copper",
  "bandwidth": "1Gbps",
  "status": "active",
  "vlan_tags": [10]
}
```

#### 3. Switch ↔ Switch (Trunk)
```json
{
  "_key": "conn_sw1_sw2",
  "_from": "devices/switch_sw1",
  "_to": "devices/switch_sw2",
  "src_port": "port8",
  "dst_port": "port8",
  "cable_type": "fiber",
  "bandwidth": "10Gbps",
  "status": "active",
  "trunk_mode": true,
  "vlan_tags": [10, 20, 30, 40]
}
```

---

## 3. Graph Definition (ArangoDB)

### Create Graph via ArangoDB Web UI

```javascript
// Navigate to Graphs tab → Create Graph

{
  "name": "network_topology",
  "edgeDefinitions": [
    {
      "collection": "connections",
      "from": ["devices"],
      "to": ["devices"]
    }
  ],
  "orphanCollections": []
}
```

### Create Graph via AQL

```aql
-- Create collections
CREATE COLLECTION devices;
CREATE COLLECTION connections EDGE;

-- Create graph
CREATE GRAPH network_topology
  EDGE DEFINITIONS (
    connections FROM devices TO devices
  );
```

---

## 4. Indexes (Performance Optimization)

```aql
-- Index on device type for filtering
CREATE INDEX device_type_idx ON devices (device_type) TYPE persistent;

-- Index on hostname for lookups
CREATE INDEX hostname_idx ON devices (hostname) TYPE persistent;

-- Index on IP address
CREATE INDEX ip_idx ON devices (ip_address) TYPE persistent;

-- Index on connection status
CREATE INDEX status_idx ON connections (status) TYPE persistent;

-- Index on ports for quick port lookups
CREATE INDEX src_port_idx ON connections (src_port) TYPE persistent;
CREATE INDEX dst_port_idx ON connections (dst_port) TYPE persistent;
```

---

## 5. Validation Rules (Application-Level)

### Device Validation
- `hostname`: Required, alphanumeric + hyphens, max 64 chars
- `device_type`: Required, enum ["router", "switch", "server"]
- `ip_address`: Required, valid IPv4 format
- `mac_address`: Required, valid MAC format (XX:XX:XX:XX:XX:XX)

### Connection Validation
- `_from` and `_to`: Must reference existing devices
- `src_port` and `dst_port`: Must exist in respective device's ports array
- No duplicate connections between same port pairs
- Prevent self-loops (device connecting to itself)

---

## 6. Sample Data Insertion

```javascript
// Insert Devices
db.devices.insert([
  {
    "_key": "router_r1",
    "hostname": "R1",
    "device_type": "router",
    "ip_address": "10.0.0.1",
    "mac_address": "00:1A:2B:3C:4D:5E",
    "ports": [{"name": "eth0"}, {"name": "eth1"}]
  },
  {
    "_key": "switch_sw1",
    "hostname": "SW1",
    "device_type": "switch",
    "ip_address": "192.168.1.10",
    "mac_address": "00:1A:2B:3C:4D:60",
    "ports": [{"name": "port1"}, {"name": "port2"}, {"name": "port3"}, {"name": "port4"}]
  },
  {
    "_key": "server_web1",
    "hostname": "WEB1",
    "device_type": "server",
    "ip_address": "192.168.10.50",
    "mac_address": "00:1A:2B:3C:4D:70",
    "ports": [{"name": "eth0"}]
  }
]);

// Insert Connections
db.connections.insert([
  {
    "_from": "devices/router_r1",
    "_to": "devices/switch_sw1",
    "src_port": "eth0",
    "dst_port": "port4",
    "cable_type": "fiber",
    "bandwidth": "10Gbps"
  },
  {
    "_from": "devices/switch_sw1",
    "_to": "devices/server_web1",
    "src_port": "port1",
    "dst_port": "eth0",
    "cable_type": "copper",
    "bandwidth": "1Gbps"
  }
]);
```

---

## Schema Design Rationale

### Why This Structure?

1. **Flexible Attributes:** JSON allows varying fields per device type without rigid schemas
2. **Port Arrays:** Each device lists available ports for validation
3. **Edge Ports:** Critical for network configs - `src_port` and `dst_port` on edges
4. **Metadata Separation:** Clean separation of network data vs. UI/admin data
5. **Graph-Native:** `_from`/`_to` fields enable efficient AQL graph traversals
6. **Extensibility:** Easy to add new device types or connection attributes

### Graph Database Advantages

- **Natural Fit:** Networks ARE graphs
- **Traversal Queries:** Find all devices reachable from router in O(V+E)
- **Relationship Storage:** Ports, VLANs, bandwidth stored on edges
- **Path Finding:** Shortest cable path, redundancy analysis
- **Hierarchy Discovery:** Automatic layer detection via traversal depth
