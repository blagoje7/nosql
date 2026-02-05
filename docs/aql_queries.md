# AQL (ArangoDB Query Language) Documentation
## NetGraph Provisioner Project

This document details the actual AQL queries used in the NetGraph Provisioner backend (`backend/app/main.py` and `backend/app/services/graph_service.py`). These queries support core features like topology discovery, path analysis, statistics, and multi-database topology management.

---

## Project Workflow & Data Persistence

### Multi-Database Architecture
The application supports multiple isolated network topologies through separate ArangoDB databases. Each database contains:
- **devices** collection (vertices in the graph)
- **connections** collection (edges in the graph)
- **audit_log** collection (change tracking)
- **network_topology** graph (links devices and connections)

### Topology Save/Load Workflow
1. **User creates topology** on the canvas (devices + connections)
2. **Click Save** → Entire topology is persisted to the active database via bulk operations
3. **Auto-reload** → After save, topology is reloaded from database to sync keys
4. **Device keys update** → Frontend nodes now use database-assigned `_key` values
5. **Path analysis** → Can now find paths using actual database keys

**Key Benefits**: 
- Device keys from the canvas match the database, enabling graph traversal queries to work correctly
- Atomic save operation (clears old data, inserts new data)
- Supports switching between multiple network topology databases
- Preserves all device properties: ports, VLANs, subnets, static routes, router IDs
- Connection metadata preserved: cable types, speeds, port mappings
- Device counters reset based on loaded topology (prevents hostname conflicts)

---

## 1. Network Statistics & Health Dashboard
**Source:** `backend/app/main.py` - `get_network_statistics`  
**Purpose:** Generates a comprehensive overview of the network state in a single query (Aggregation & Analytics).

```aql
LET total_devices = LENGTH(FOR d IN devices RETURN 1)
LET total_connections = LENGTH(FOR c IN connections RETURN 1)

// Group devices by type
LET devices_by_type = (
    FOR d IN devices
        COLLECT device_type = d.device_type WITH COUNT INTO count
        SORT count DESC
        RETURN {
            type: device_type,
            count: count
        }
)

// Group connections by cable type
LET connections_by_cable = (
    FOR c IN connections
        COLLECT cable_type = c.cable_type WITH COUNT INTO count
        SORT count DESC
        RETURN {
            cable_type: cable_type || "unknown",
            count: count
        }
)

// Calculate connectivity per device (Degree Centrality)
LET device_connections = (
    FOR d IN devices
        LET outgoing = LENGTH(
            FOR c IN connections
                FILTER c._from == d._id
                RETURN 1
        )
        LET incoming = LENGTH(
            FOR c IN connections
                FILTER c._to == d._id
                RETURN 1
        )
        LET total = outgoing + incoming
        RETURN {
            device_key: d._key,
            hostname: d.hostname,
            device_type: d.device_type,
            connection_count: total
        }
)

// Top 5 most connected devices
LET most_connected = (
    FOR dc IN device_connections
        SORT dc.connection_count DESC
        LIMIT 5
        RETURN dc
)

// Find isolated devices (Orphans)
LET isolated_devices = (
    FOR dc IN device_connections
        FILTER dc.connection_count == 0
        RETURN {
            key: dc.device_key,
            hostname: dc.hostname,
            type: dc.device_type
        }
)

// Average connectivity
LET avg_connections = AVG(
    FOR dc IN device_connections
        RETURN dc.connection_count
)

// Port Statistics Aggregation
LET port_stats = (
    FOR d IN devices
        LET port_count = LENGTH(d.ports || [])
        COLLECT device_type = d.device_type
        AGGREGATE 
            total_ports = SUM(port_count),
            avg_ports = AVG(port_count),
            device_count = LENGTH(1)
        RETURN {
            device_type: device_type,
            total_ports: total_ports,
            average_ports_per_device: avg_ports,
            device_count: device_count
        }
)

// VLAN Statistics
LET vlan_stats = (
    FOR d IN devices
        FILTER LENGTH(d.vlans || []) > 0
        LET vlan_count = LENGTH(d.vlans)
        COLLECT device_type = d.device_type
        AGGREGATE 
            devices_with_vlans = LENGTH(1),
            total_vlans = SUM(vlan_count)
        RETURN {
            device_type: device_type,
            devices_with_vlans: devices_with_vlans,
            total_vlans: total_vlans
        }
)

// Static Route Statistics
LET route_stats = (
    FOR d IN devices
        FILTER LENGTH(d.static_routes || []) > 0
        LET route_count = LENGTH(d.static_routes)
        COLLECT device_type = d.device_type
        AGGREGATE 
            devices_with_routes = LENGTH(1),
            total_routes = SUM(route_count)
        RETURN {
            device_type: device_type,
            devices_with_routes: devices_with_routes,
            total_routes: total_routes
        }
)

RETURN {
    overview: {
        total_devices: total_devices,
        total_connections: total_connections,
        average_connections_per_device: avg_connections,
        isolated_device_count: LENGTH(isolated_devices)
    },
    devices_by_type: devices_by_type,
    connections_by_cable_type: connections_by_cable,
    most_connected_devices: most_connected,
    isolated_devices: isolated_devices,
    port_statistics: port_stats,
    vlan_statistics: vlan_stats,
    route_statistics: route_stats
}
```

---

## 2. Advanced Path Analysis with Cost Calculation
**Source:** `backend/app/main.py` - `analyze_paths`  
**Purpose:** Finds Shortest, Cheapest, and Alternative paths between two nodes. Calculates cost based on link speed.

**Important:** Uses `ANY` direction for traversal (not `OUTBOUND`) because network cables are bidirectional - data can flow in both directions regardless of how the edge is stored in the database.

```aql
LET source_id = @source_id
LET target_id = @target_id

// 1. Find ALL paths (Depth limited to 10 hops)
// Using ANY direction to simulate physical cabling which is bidirectional
LET all_paths = (
    FOR v, e, p IN 1..10 ANY source_id GRAPH 'network_topology'
        FILTER v._id == target_id
        LIMIT 20
        RETURN {
            vertices: p.vertices,
            edges: p.edges,
            hop_count: LENGTH(p.edges)
        }
)

// 2. Calculate Cost per Path based on Speed
// Cost Logic: 10G+ = 1 (Best), 1G = 5, 100M = 10, 10M = 20 (Worst)
LET paths_with_cost = (
    FOR path IN all_paths
        LET total_cost = SUM(
            FOR edge IN path.edges
                LET speed = edge.speed || "1G"
                LET cost = (
                    speed == "10G" OR speed == "25G" OR speed == "40G" OR speed == "100G" ? 1 :
                    speed == "1G" ? 5 :
                    speed == "100M" ? 10 :
                    20
                )
                RETURN cost
        )
        RETURN MERGE(path, {
            total_cost: total_cost,
            avg_cost: total_cost / path.hop_count
        })
)

// 3. Select Strategies
// Shortest (Fewest Hops)
LET shortest = (
    FOR path IN paths_with_cost
        SORT path.hop_count ASC, path.total_cost ASC
        LIMIT 1
        RETURN path
)[0]

// Cheapest (Highest Bandwidth)
LET cheapest = (
    FOR path IN paths_with_cost
        SORT path.total_cost ASC, path.hop_count ASC
        LIMIT 1
        RETURN path
)[0]

// Alternatives (Not shortest, not cheapest)
LET alternatives = (
    FOR path IN paths_with_cost
        FILTER path != shortest AND path != cheapest
        SORT path.hop_count ASC, path.total_cost ASC
        LIMIT 5
        RETURN path
)

RETURN {
    source: DOCUMENT(source_id),
    target: DOCUMENT(target_id),
    shortestPath: shortest,
    cheapestPath: cheapest,
    alternativePaths: alternatives,
    totalPathsFound: LENGTH(all_paths)
}
```

---

## 3. Bulk Topology Save & Load Operations
**Source:** `backend/app/main.py` - `save_topology`, `get_full_topology`  
**Purpose:** Efficiently persist and retrieve entire network topologies as a single operation.

### Save Topology (Clear & Insert)
Clears existing data and inserts new devices and connections:

```aql
// Clear existing devices
FOR d IN devices 
    REMOVE d IN devices

// Clear existing connections
FOR c IN connections 
    REMOVE c IN connections
```

Then performs bulk inserts using the Python driver's `insert()` method for each device and connection. After saving, an audit log entry is created to track the bulk operation:

```python
log_audit_event('bulk_save', 'topology', 'full_topology', {
    'device_count': len(device_results),
    'connection_count': len(connection_results),
    'device_keys': [d['_key'] for d in device_results],
    'connection_keys': [c['_key'] for c in connection_results]
})
```

### Load Topology
Retrieves all devices and connections:

```aql
// Get all devices
FOR d IN devices
    RETURN d

// Get all connections  
FOR c IN connections
    RETURN c
```

The frontend receives both collections and reconstructs the graph visualization with proper positioning, device properties, and connection styling.

---

## 4. Port & Connection Mapping (Configuration Generation)
**Source:** `backend/app/services/graph_service.py` - `get_port_connection_map`  
**Purpose:** Builds a detailed map of every device and its neighbors, including specific port pairings (e.g., Device A [Port 1] <-> Device B [Port 2]). Used for generating configuration files.

```aql
FOR device IN devices
  LET connections = (
    FOR v, e IN 1..1 ANY device._id
      GRAPH 'network_topology'
      // Determine local and neighbor ports from the edge
      LET my_port = e._from == device._id ? e.src_port : e.dst_port
      LET neighbor_port = e._from == device._id ? e.dst_port : e.src_port
      RETURN {
        neighbor_key: v._key,
        neighbor_hostname: v.hostname,
        neighbor_ip: v.ip_address,
        neighbor_type: v.device_type,
        my_port: my_port,
        neighbor_port: neighbor_port,
        cable_type: e.cable_type,
        speed: e.speed,
        duplex: e.duplex,
        vlan_tags: e.vlan_tags
      }
  )
  RETURN {
    _key: device._key,
    hostname: device.hostname,
    device_type: device.device_type,
    ip_address: device.ip_address,
    mac_address: device.mac_address,
    subnet_mask: device.subnet_mask,
    gateway: device.gateway,
    ports: device.ports,
    connections: connections,
    metadata: device.metadata
  }
```

---

## 5. Cascading Deletion
**Source:** `backend/app/main.py` - `delete_device`  
**Purpose:** Safely removes a device and cleans up related IP configurations on neighbor interfaces.

1. **Find Connections:**
```aql
FOR e IN connections
    FILTER e._from == CONCAT('devices/', @key) OR e._to == CONCAT('devices/', @key)
    RETURN e
```
2. **Remove Connection Edge:**
```aql
REMOVE @conn IN connections
```
*(Note: Neighbor interface IP cleanup is handled via application logic based on these query results)*

**Audit Tracking:** Both device and connection deletions are logged to the audit_log collection with full entity data snapshots.

---

## 6. Audit Log Filtering
**Source:** `backend/app/main.py` - `get_audit_log`  
**Purpose:** Retrieve audit logs with dynamic filtering.

```aql
FOR doc IN audit_log
    FILTER doc.action == @action AND doc.entity_type == @entity_type
    SORT doc.timestamp DESC
    LIMIT @limit
    RETURN doc
```

## 7. Audit Log Statistics
**Source:** `backend/app/main.py` - `get_audit_log_stats`  
**Purpose:** Overview of system activity.

```aql
LET total = LENGTH(FOR doc IN audit_log RETURN 1)

LET by_action = (
    FOR doc IN audit_log
        COLLECT action = doc.action WITH COUNT INTO count
        RETURN {action: action, count: count}
)

LET by_entity = (
    FOR doc IN audit_log
        COLLECT entity_type = doc.entity_type WITH COUNT INTO count
        RETURN {entity_type: entity_type, count: count}
)

LET recent = (
    FOR doc IN audit_log
        SORT doc.timestamp DESC
        LIMIT 10
        RETURN {
            action: doc.action,
            entity_type: doc.entity_type,
            entity_id: doc.entity_id,
            timestamp: doc.timestamp
        }
)

RETURN {
    total: total,
    by_action: by_action,
    by_entity_type: by_entity,
    recent_activity: recent
}
```

---

## Summary: NoSQL Database Features Demonstrated

This project showcases key ArangoDB capabilities and NoSQL database concepts:

### 1. **Multi-Model Database**
- **Graph Model**: Devices (vertices) + Connections (edges) = Network topology
- **Document Model**: Audit logs, device properties, nested arrays (ports, VLANs, routes)
- **Key-Value Access**: Direct device lookup by `_key`

### 2. **Graph Database Advantages**
- **Native Graph Traversal**: `ANY`, `OUTBOUND`, `INBOUND` traversal with depth limits
- **Path Finding**: Shortest path, cheapest path algorithms in pure AQL
- **Relationship Modeling**: Natural representation of network connectivity
- **Bidirectional Edges**: Same edge used for both directions (physical reality)

### 3. **AQL Query Power**
- **Complex Aggregations**: Statistics calculated in single query (devices by type, connection counts)
- **Nested Subqueries**: LET statements for intermediate calculations
- **Cost-Based Algorithms**: Custom scoring logic (cable speed → cost)
- **Filtering & Sorting**: Dynamic queries with bind parameters

### 4. **Operational Features**
- **Multi-Database Support**: Isolated topologies per database
- **Bulk Operations**: Atomic clear + insert for topology saves
- **Audit Logging**: Complete change tracking with timestamps
- **Index Performance**: Efficient queries on action, entity_type, timestamp

### 5. **Scalability Considerations**
- Depth limits prevent infinite loops in cyclic graphs
- Result limits (LIMIT 20) for path queries
- Efficient aggregation using COLLECT
- Indexed lookups for large topologies

This architecture demonstrates why graph databases excel at network topology management compared to traditional RDBMS solutions.

````