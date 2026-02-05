# NetGraph Provisioner - ArangoDB Network Topology Manager

## Project Overview
A web application for designing network topologies and generating configuration scripts using ArangoDB's Graph capabilities.

**Course:** NoSQL Databases (University Project)  
**Database:** ArangoDB (Graph Database)  
**Backend:** Python (FastAPI)  
**Frontend:** React + React Flow

---

## 1. ArangoDB Data Model (Graph Schema)

### Database Structure
- **Database Name:** `netgraph_db`
- **Graph Name:** `network_topology`
- **Vertex Collection:** `devices` (routers, switches, servers)
- **Edge Collection:** `connections` (cables/links with port information)

### Why Graph Database?
- **Natural Representation:** Networks are inherently graphs (devices as vertices, cables as edges)
- **Efficient Traversals:** AQL graph queries for finding all connected devices, shortest paths, network segments
- **Port Relationships:** Edge attributes store crucial port mappings (eth0 → port1)
- **Hierarchy Discovery:** Identify network layers (core routers → distribution switches → access switches → servers)

---

## 2. Implementation Architecture

### Project Structure
```
netgraph-provisioner/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── database.py          # ArangoDB connection
│   │   ├── models.py            # Pydantic models
│   │   ├── routers/
│   │   │   ├── topology.py      # CRUD for topology
│   │   │   └── export.py        # Config generation
│   │   └── services/
│   │       ├── graph_service.py # Graph operations
│   │       └── config_generator.py
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Canvas.jsx       # React Flow canvas
│   │   │   ├── DeviceNode.jsx   # Custom node component
│   │   │   └── Sidebar.jsx      # Device palette
│   │   ├── services/
│   │   │   └── api.js           # Backend API calls
│   │   └── App.jsx
│   └── package.json
├── docs/
│   ├── schema.md
│   └── queries.md
└── README.md
```

### Data Flow
1. **Design:** User creates topology in React Flow → Local state (nodes/edges JSON)
2. **Save:** Frontend POST `/api/topology` → Backend transforms to ArangoDB format → Save to Graph
3. **Export:** User clicks "Generate" → Backend runs AQL traversal → Generate config file → Return as download

---

## 3. Mapping React Flow ↔ ArangoDB

### React Flow Format
```json
{
  "nodes": [
    {"id": "n1", "type": "router", "data": {"hostname": "R1", "ip": "192.168.1.1"}, "position": {"x": 100, "y": 100}}
  ],
  "edges": [
    {"id": "e1", "source": "n1", "target": "n2", "data": {"srcPort": "eth0", "dstPort": "port1"}}
  ]
}
```

### ArangoDB Transformation
- **Node → Device Vertex:** Use React Flow node ID as `_key`, copy all `data` fields
- **Edge → Connection Edge:** `_from: "devices/n1"`, `_to: "devices/n2"`, store port data

---

## 4. Key Features Demonstrating Graph Capabilities

### Graph Traversals
- **Full Topology Discovery:** From any router, find all reachable devices
- **Shortest Path:** Find shortest cable path between two devices
- **Network Segments:** Identify all devices in a subnet using traversal filters
- **Depth-First Walk:** Generate hierarchical configs (routers → switches → servers)

### Edge Attributes (Critical for Networking)
- **Port Mapping:** Store `src_port` and `dst_port` on each connection edge
- **Cable Type:** fiber, copper, wireless
- **Bandwidth:** 1Gbps, 10Gbps
- **VLAN Tags:** For layer 2 segmentation

---

## 5. Configuration Generation Examples

### Ansible Inventory
```ini
[routers]
R1 ansible_host=192.168.1.1

[switches]
SW1 ansible_host=192.168.1.10

[R1:vars]
eth0_connected_to=SW1:port1
```

### Shell Script (Basic Config)
```bash
# Router R1 Configuration
ifconfig eth0 192.168.1.1 netmask 255.255.255.0 up
# Connected to SW1:port1
```

---

## 6. Setup Instructions

### ArangoDB Setup
```bash
# Pull Docker image
docker pull arangodb/arangodb:latest

# Run ArangoDB
docker run -e ARANGO_ROOT_PASSWORD=netgraph123 -p 8529:8529 arangodb/arangodb:latest

# Access Web UI: http://localhost:8529
# Username: root, Password: netgraph123
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

---

## 7. Grading Criteria Alignment

✅ **Graph Database Usage:** Full graph implementation with vertices, edges, and traversals  
✅ **AQL Queries:** Complex traversals demonstrating NoSQL query power  
✅ **Real-World Application:** Network topology modeling is industry-relevant  
✅ **Data Modeling:** Proper schema design with relationships  
✅ **Functionality:** Complete CRUD + graph traversal + export feature

---

## 8. Advanced Features (NoSQL Showcase)

### Network Path Analysis (Graph Traversal)
Demonstrates ArangoDB's powerful graph traversal capabilities:

**Feature:** Find all possible paths between two devices
- **Shortest Path:** Minimum number of hops (highlighted in green)
- **Cheapest Path:** Lowest cost based on cable speeds (highlighted in red)
  - Cost calculation: 10G/25G/40G/100G = 1, 1G = 5, 100M = 10, 10M = 20
- **Alternative Paths:** All other valid routes (highlighted in yellow)

**Technical Implementation:**
```aql
FOR v, e, p IN 1..10 OUTBOUND @source_id GRAPH 'network_topology'
  FILTER v._id == @target_id
  RETURN p
```

**Usage:**
1. Click on any device in the topology
2. Go to "Paths" tab in properties panel
3. Select destination device
4. View all paths with hop counts and costs
5. Click "Highlight on Canvas" to visualize paths with color coding

### Audit Log (Change Streams)
Tracks all topology modifications with timestamps:
- Device creation/deletion
- Connection changes
- Bulk topology saves
- Provides complete audit trail for compliance

### Network Statistics (Aggregation Queries)
Real-time analytics using AQL aggregations:
- Devices by type with counts
- Connection statistics (by cable type, speed)
- Port utilization analysis
- VLAN and routing statistics
- Isolated device detection

---

## 9. Future Enhancements (Optional)
- Import existing network configs (parse and visualize)
- Cycle detection (prevent network loops)
- Shortest path visualization
- Multi-topology support (production vs. staging)
- Real-time collaboration

---

## License
Educational Project - NoSQL Databases Course
