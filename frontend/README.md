# NetGraph Provisioner - Frontend (Vue 3)

Network Topology Designer with Vue 3 + Vue Flow + ArangoDB

## Features

- 🎨 Drag-and-drop canvas with Vue Flow
- 🔷 Add Routers, Switches, Servers
- 🔌 Connect devices with port mapping
- ✏️ Edit device properties (IP, hostname, MAC)
- 💾 Save topology to ArangoDB
- 📥 Export configs (Ansible, Shell, Cisco, JSON)

## Quick Start

### Install Dependencies
```bash
npm install
```

### Start Development Server
```bash
npm run dev
```

Open: http://localhost:5173

### Build for Production
```bash
npm run build
```

## Usage

1. **Add Devices**: Click device types in left sidebar (Router, Switch, Server)
2. **Connect**: Drag between nodes to create connections
3. **Edit Properties**: Click node → Edit in right panel
4. **Save**: Click "Save Topology" to persist to ArangoDB
5. **Export**: Click "Export Config" → Select format → Download

## Tech Stack

- **Vue 3** - Frontend framework
- **Vue Flow** - Interactive node-based UI
- **Axios** - HTTP client
- **Pinia** - State management (optional)
- **Vite** - Build tool

## API Integration

Backend API must be running on `http://localhost:8000`

See: `backend/app/main.py`

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── TopologyCanvas.vue    # Main canvas
│   │   ├── DeviceSidebar.vue     # Device palette
│   │   ├── PropertiesPanel.vue   # Edit properties
│   │   └── ExportModal.vue       # Export dialog
│   ├── services/
│   │   └── api.js                # Backend API calls
│   ├── App.vue                   # Main app
│   └── main.js                   # Entry point
├── package.json
└── vite.config.js
```

## Configuration

Create `.env` file:
```
VITE_API_BASE=http://localhost:8000/api
```

## Canvas Shortcuts

- **Left Click**: Select node
- **Right Click**: Delete node
- **Drag Node**: Move device
- **Drag Handle**: Connect devices
- **Mouse Wheel**: Zoom in/out
- **Middle Click + Drag**: Pan canvas

## Device Types

### Router 🔷
- Default ports: eth0, eth1
- Default IP: 10.0.0.x
- Color: Blue

### Switch 🔶
- Default ports: port1-4
- Default IP: 192.168.1.x
- Color: Green

### Server 🖥️
- Default ports: eth0
- Default IP: 192.168.10.x
- Color: Orange

## Export Formats

1. **Ansible Inventory** - `.ini` file with port variables
2. **Shell Script** - `.sh` with ifconfig commands
3. **Cisco IOS** - `.txt` router/switch configs
4. **Text Diagram** - `.txt` ASCII visualization
5. **JSON** - `.json` complete export

## Development

### Add New Device Type
1. Update `deviceCounters` in `TopologyCanvas.vue`
2. Add color scheme in `style.css`
3. Add to `DeviceSidebar.vue`

### Customize Node Appearance
Edit `.custom-node` styles in `style.css`

### Add New Export Format
1. Add format to backend `config_generator.py`
2. Add option to `ExportModal.vue`

## Troubleshooting

### Backend Connection Failed
- Ensure backend is running: `uvicorn app.main:app --reload`
- Check CORS settings in `backend/app/main.py`

### Nodes Not Connecting
- Ensure both devices have ports defined
- Check browser console for errors

### Export Not Working
- Verify topology has devices
- Check backend logs for AQL errors

## License

Educational Project - NoSQL Databases Course
