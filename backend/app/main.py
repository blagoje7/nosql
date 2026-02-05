# backend/app/main.py
"""
FastAPI Glavna Aplikacija - NetGraph Provisioner
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field, ValidationError, ConfigDict
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.database import get_db, get_devices_collection, get_connections_collection, list_databases, create_database, connect_to_database, get_current_database_name, log_audit_event, get_audit_log_collection
from app.services.graph_service import GraphService
from app.services.config_generator import generate_config_from_graph
from arango.database import StandardDatabase

# Inicijalizacija FastAPI aplikacije
app = FastAPI(
    title="NetGraph Provisioner API",
    description="Network Topology Designer with ArangoDB Graph Database",
    version="1.0.0"
)

# CORS middleware za React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React razvojni serveri
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Modeli
class Port(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    name: str
    type: str = "ethernet"
    speed: str = "1Gbps"
    status: str = "up"
    
    # Layer 3 konfiguracija (IP adresiranje)
    ip_address: Optional[str] = None
    subnet_mask: Optional[str] = None
    
    # Switch VLAN konfiguracija (Layer 2)
    mode: Optional[str] = None  # "access", "trunk", ili None
    vlan: Optional[str] = None  # VLAN ID ili opseg (npr., "10" ili "10,20,30-40")
    
    # Svojstva podinterfejsa rutera
    encapsulation: Optional[str] = None  # "dot1q" za 802.1Q tagovanje
    vlan_id: Optional[int] = None  # VLAN ID za podinterfejs
    
    # SVI (Switch Virtual Interface) - za Layer 3 na svičevima
    is_svi: bool = False  # True ako je ovo VLAN interfejs (interface vlan X)
    is_routed: bool = False  # True ako je ovo L3 svič port u rutiranom modu
    description: Optional[str] = None  # Opis interfejsa


class Subnet(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    network: str  # Mrežna adresa (npr., "192.168.10.0")
    mask: str  # Subnet maska (npr., "255.255.255.0")
    gateway: str  # Gateway IP adresa
    vlan_id: Optional[int] = None  # Povezani VLAN ID
    description: Optional[str] = None  # Opis subneta


class StaticRoute(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    destination_network: str  # Odredišna mreža (npr., "192.168.20.0" ili "0.0.0.0" za default)
    subnet_mask: str  # Subnet maska (npr., "255.255.255.0" ili "0.0.0.0" za default)
    next_hop: Optional[str] = None  # Next-hop IP adresa (npr., "10.0.0.2")
    exit_interface: Optional[str] = None  # Ime izlaznog interfejsa (npr., "GigabitEthernet0/0")
    metric: Optional[int] = 1  # Administrativna distanca/metrika (podrazumevano: 1)
    description: Optional[str] = None  # Opis rute


class Vlan(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    vlan_id: int  # VLAN ID (1-4094)
    name: str  # Ime VLAN-a (npr., "Management", "Sales")
    status: str = "active"  # Status VLAN-a: "active" ili "suspended"
    description: Optional[str] = None  # Opis VLAN-a


class DeviceCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    key: str = Field(..., alias="_key")
    hostname: str
    device_type: str  # ruter, svič, server
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    subnet_mask: str = "255.255.255.0"
    gateway: Optional[str] = None
    router_id: Optional[str] = None  # Router ID za ruting protokole (OSPF, EIGRP, BGP)
    ports: List[Port] = []
    subnets: List[Subnet] = []
    static_routes: List[StaticRoute] = []
    vlans: List[Vlan] = []
    ui_position: Optional[Dict[str, float]] = None
    metadata: Optional[Dict[str, Any]] = None


class ConnectionCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    key: str = Field(..., alias="_key")
    from_device: str = Field(..., alias="_from")
    to_device: str = Field(..., alias="_to")
    src_port: str
    dst_port: str
    cable_type: str = "Cat6"  # Cat5e, Cat6, Cat6a, Cat7, Fiber-SM, Fiber-MM, DAC
    speed: str = "1G"  # Dogovorena brzina: 10M, 100M, 1G, 10G, 25G, 40G, 100G
    duplex: str = "auto"  # full, half, auto
    status: str = "active"
    vlan_tags: Optional[List[int]] = None
    subnet: Optional[str] = None
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None


class TopologySave(BaseModel):
    devices: List[DeviceCreate]
    connections: List[ConnectionCreate]

class DatabaseCreate(BaseModel):
    name: str
    description: Optional[str] = ""


class ConfigExportRequest(BaseModel):
    format: str = "cisco"  # cisco, diagram, json
    start_device_key: Optional[str] = None


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "NetGraph Provisioner API", "version": "1.0.0"}


# Endpointi za upravljanje bazom podataka
@app.get("/api/databases")
def list_all_databases():
    """Izlistavanje svih NetGraph baza podataka"""
    try:
        databases = list_databases()
        return {"databases": databases}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/databases")
def create_new_database(database: DatabaseCreate):
    """Kreiranje nove ArangoDB baze podataka"""
    try:
        # Generisanje imena baze podataka
        db_name = database.name.lower().replace(' ', '_').replace('-', '_')
        db_name = ''.join(c for c in db_name if c.isalnum() or c == '_')
        db_name = f"netgraph_{db_name}"
        
        # Kreiranje baze podataka (ovo će takođe kreirati kolekcije i graf)
        create_database(db_name)
        
        return {
            "message": "Database created successfully",
            "database": db_name
        }
    except Exception as e:
        if "already exists" in str(e):
            raise HTTPException(status_code=400, detail="Database already exists")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/databases/connect")
def connect_database(database_name: str):
    """Povezivanje sa određenom bazom podataka"""
    try:
        connect_to_database(database_name)
        return {
            "message": f"Connected to database '{database_name}'",
            "database": database_name
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/databases/current")
def get_current_db():
    """Dobijanje trenutno povezane baze podataka"""
    try:
        db_name = get_current_database_name()
        if db_name:
            return {"database": db_name}
        else:
            raise HTTPException(status_code=400, detail="No database connected")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/health")
@app.get("/health")
def health_check(db: StandardDatabase = Depends(get_db)):
    try:
        # Testiranje veze sa bazom podataka
        db.version()
        return {
            "status": "healthy", 
            "database": "connected",
            "message": "NetGraph Provisioner API",
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unhealthy: {str(e)}")


# Operacije sa uređajima
@app.delete("/api/devices/{device_key}")
def delete_device(device_key: str, db: StandardDatabase = Depends(get_db)):
    """Brisanje uređaja i čišćenje konekcija/IP adresa"""
    try:
        devices_col = get_devices_collection()
        
        # Prvo provera da li uređaj postoji
        device = devices_col.get(device_key)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_key}' not found")
        
        # 1. Pronalazak svih konekcija ka ovom uređaju
        query = """
        FOR e IN connections
            FILTER e._from == CONCAT('devices/', @key) OR e._to == CONCAT('devices/', @key)
            RETURN e
        """
        cursor = db.aql.execute(query, bind_vars={'key': device_key})
        connections = [doc for doc in cursor]
        
        # 2. Za svaku konekciju, pronalazak SUSEDA i brisanje IP adrese njegovog porta
        for conn in connections:
            # Određivanje ID-a suseda i porta suseda
            is_from = conn['_from'] == f'devices/{device_key}'
            neighbor_id = conn['_to'] if is_from else conn['_from']
            neighbor_key = neighbor_id.split('/')[-1]
            neighbor_port_name = conn['dst_port'] if is_from else conn['src_port']
            
            # Dobavljanje susednog uređaja
            neighbor = devices_col.get(neighbor_key)
            
            if neighbor and 'ports' in neighbor:
                updated_ports = []
                data_changed = False
                for p in neighbor['ports']:
                    if p['name'] == neighbor_port_name and p.get('ip_address'):
                        # Brisanje IP adrese
                        p['ip_address'] = ""
                        p['subnet_mask'] = ""
                        data_changed = True
                    updated_ports.append(p)
                
                if data_changed:
                    neighbor['ports'] = updated_ports
                    devices_col.update(neighbor)
            
            # Brisanje same konekcije
            db.aql.execute("REMOVE @conn IN connections", bind_vars={'conn': conn['_key']})

        # 3. Brisanje samog uređaja
        devices_col.delete(device_key)
        
        # Beleženje događaja revizije
        log_audit_event('delete', 'device', device_key, device)
        
        return {"message": "Device and associated connections deleted", "key": device_key}
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Operacije sa konekcijama
@app.delete("/api/connections/{connection_key}")
def delete_connection(connection_key: str, db: StandardDatabase = Depends(get_db)):
    """Brisanje konekcije i brisanje IP adresa na oba porta"""
    try:
        connections_col = get_connections_collection()
        devices_col = get_devices_collection()
        
        conn = connections_col.get(connection_key)
        if not conn:
            raise HTTPException(status_code=404, detail="Connection not found")
            
        # Pomoćna funkcija za brisanje IP adrese porta
        def clear_device_port(device_id, port_name):
            key = device_id.split('/')[-1]
            device = devices_col.get(key)
            if device and 'ports' in device:
                updated_ports = []
                changed = False
                for p in device['ports']:
                    if p['name'] == port_name and p.get('ip_address'):
                        p['ip_address'] = ""
                        p['subnet_mask'] = ""
                        changed = True
                    updated_ports.append(p)
                if changed:
                    device['ports'] = updated_ports
                    devices_col.update(device)

        # Brisanje IP adresa na oba kraja
        clear_device_port(conn['_from'], conn['src_port'])
        clear_device_port(conn['_to'], conn['dst_port'])

        # Brisanje konekcije
        connections_col.delete(connection_key)
        
        # Beleženje događaja revizije
        log_audit_event('delete', 'connection', connection_key, conn)
        
        return {"message": "Connection deleted an IPs cleared", "key": connection_key}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Operacije topologije (Masovno čuvanje)
@app.post("/api/topology/save")
def save_topology(topology: TopologySave, db: StandardDatabase = Depends(get_db)):
    """Čuvanje celokupne topologije (uređaji + konekcije) u trenutnu bazu podataka - Transakciono"""
    try:
        # 0. Dobavljanje postojećih ključeva za detekciju novih entiteta (za audit log)
        try:
            cursor_d = db.aql.execute("FOR d IN devices RETURN d._key")
            existing_device_keys = set([k for k in cursor_d])
            
            cursor_c = db.aql.execute("FOR c IN connections RETURN c._key")
            existing_connection_keys = set([k for k in cursor_c])
        except Exception:
            # Ako kolekcije još ne postoje (prvo snimanje), skupovi su prazni
            existing_device_keys = set()
            existing_connection_keys = set()

        # 1. Priprema podataka za masovni unos
        devices_list = []
        for device in topology.devices:
            d = device.model_dump(by_alias=True)
            d['created_at'] = datetime.now().isoformat()
            devices_list.append(d)
        
        connections_list = []
        for connection in topology.connections:
            c = connection.model_dump(by_alias=True)
            c['created_at'] = datetime.now().isoformat()
            connections_list.append(c)

        # 2. Izvršavanje transakcije na serveru
        # Koristimo Python-Arango Stream Transactions (ne Javascript)
        txn = db.begin_transaction(write=['devices', 'connections'])
        try:
            # Povezivanje kolekcija sa transakcijom
            devices_col = txn.collection('devices')
            connections_col = txn.collection('connections')
            
            # Brisanje postojećih podataka (AQL unutar transakcije)
            txn.aql.execute("FOR d IN devices REMOVE d IN devices")
            txn.aql.execute("FOR c IN connections REMOVE c IN connections")
            
            # Unos novih podataka (Bulk Insert)
            # Koristimo insert_many koji je stabilniji unutar transakcija od import_bulk
            if devices_list:
                devices_col.insert_many(devices_list, overwrite=True)
            
            if connections_list:
                connections_col.insert_many(connections_list, overwrite=True)
                
            # Potvrda transakcije
            txn.commit_transaction()
            
            # 3. Detekcija i beleženje novokreiranih entiteta (Audit Log)
            # Ovo radimo nakon uspešne transakcije
            new_audit_entries = []
            current_time = datetime.now().isoformat()
            db_name = get_current_database_name()

            # Detekcija novih uređaja
            for device in topology.devices:
                if device.key not in existing_device_keys:
                    new_audit_entries.append({
                        'action': 'create',
                        'entity_type': 'device',
                        'entity_id': device.key,
                        'entity_data': {
                            'hostname': device.hostname,
                            'type': device.device_type,
                            'ip': device.ip_address
                        },
                        'user': 'system',
                        'timestamp': current_time,
                        'database': db_name
                    })

            # Detekcija novih konekcija
            for conn in topology.connections:
                if conn.key not in existing_connection_keys:
                    new_audit_entries.append({
                        'action': 'create',
                        'entity_type': 'connection',
                        'entity_id': conn.key,
                        'entity_data': {
                            'from_device': conn.from_device.split('/')[-1] if '/' in conn.from_device else conn.from_device,
                            'to_device': conn.to_device.split('/')[-1] if '/' in conn.to_device else conn.to_device,
                            'src_port': conn.src_port,
                            'dst_port': conn.dst_port,
                            'cable_type': conn.cable_type
                        },
                        'user': 'system',
                        'timestamp': current_time,
                        'database': db_name
                    })
            
            # Masovni unos audit logova ako ih ima
            if new_audit_entries:
                try:
                    audit_col = get_audit_log_collection()
                    audit_col.import_bulk(new_audit_entries)
                except Exception as e:
                    print(f"Failed to save granular audit logs: {e}")

        except Exception as e:
            # Poništavanje transakcije u slučaju greške
            txn.abort_transaction()
            raise e
        
        # Beleženje masovnog čuvanja topologije u reviziju (uspešna transakcija)
        log_audit_event('bulk_save', 'topology', 'full_topology', {
            'device_count': len(devices_list),
            'connection_count': len(connections_list),
            'device_keys': [d['_key'] for d in devices_list],
            'connection_keys': [c['_key'] for c in connections_list]
        })
        
        return {
            "message": "Topology saved successfully (Transaction Committed)",
            "devices_created": len(devices_list),
            "connections_created": len(connections_list)
        }
    
    except ValidationError as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))


# Endpoint za učitavanje topologije
@app.get("/api/graph/topology")
def get_full_topology(start_device_key: Optional[str] = None, db: StandardDatabase = Depends(get_db)):
    """Dobijanje pune topologije iz trenutne baze podataka"""
    try:
        devices_col = get_devices_collection()
        connections_col = get_connections_collection()
        
        devices = list(devices_col.all())
        connections = list(connections_col.all())
        
        return {"topology": {"devices": devices, "connections": connections}}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Izvoz konfiguracije
@app.post("/api/export/config")
def export_config(request: ConfigExportRequest, db: StandardDatabase = Depends(get_db)):
    """
    Generisanje konfiguracionog fajla iz topologije
    Podržava: cisco, diagram, json
    """
    try:
        graph_service = GraphService(db)
        
        # Dobavljanje podataka topologije
        devices_data = graph_service.get_port_connection_map()
        
        if not devices_data:
            raise HTTPException(status_code=404, detail="No devices found in topology")
        
        # Generisanje konfiguracije u traženom formatu
        config_content = generate_config_from_graph(devices_data, request.format)
        
        # Postavljanje odgovarajućeg tipa sadržaja
        content_types = {
            "cisco": "text/plain",
            "diagram": "text/plain",
            "json": "application/json"
        }
        
        filenames = {
            "cisco": "config.txt",
            "diagram": "topology.txt",
            "json": "topology.json"
        }
        
        return Response(
            content=config_content,
            media_type=content_types.get(request.format, "text/plain"),
            headers={
                "Content-Disposition": f"attachment; filename={filenames.get(request.format, 'config.txt')}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mrežna Statistika
@app.get("/api/statistics/network")
def get_network_statistics(db: StandardDatabase = Depends(get_db)):
    """
    Dobijanje sveobuhvatne statistike mrežne topologije koristeći AQL agregacije
    
    Vraća:
    - Ukupan broj uređaja
    - Uređaji grupisani po tipu
    - Ukupan broj konekcija
    - Konekcije grupisane po tipu kabla
    - Prosečan broj konekcija po uređaju
    - Najpovezaniji uređaji (top 5)
    - Izolovani uređaji (bez konekcija)
    - Dubina mreže (max skokova)
    """
    try:
        devices_col = get_devices_collection()
        connections_col = get_connections_collection()
        
        # Složen AQL upit agregacije
        query = """
        LET total_devices = LENGTH(FOR d IN devices RETURN 1)
        LET total_connections = LENGTH(FOR c IN connections RETURN 1)
        
        // Uređaji po tipu
        LET devices_by_type = (
            FOR d IN devices
                COLLECT device_type = d.device_type WITH COUNT INTO count
                SORT count DESC
                RETURN {
                    type: device_type,
                    count: count
                }
        )
        
        // Konekcije po tipu kabla
        LET connections_by_cable = (
            FOR c IN connections
                COLLECT cable_type = c.cable_type WITH COUNT INTO count
                SORT count DESC
                RETURN {
                    cable_type: cable_type || "unknown",
                    count: count
                }
        )
        
        // Stepen povezanosti po uređaju (ulazne + izlazne konekcije)
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
        
        // Najpovezaniji uređaji (top 5)
        LET most_connected = (
            FOR dc IN device_connections
                SORT dc.connection_count DESC
                LIMIT 5
                RETURN dc
        )
        
        // Izolovani uređaji (bez konekcija)
        LET isolated_devices = (
            FOR dc IN device_connections
                FILTER dc.connection_count == 0
                RETURN {
                    key: dc.device_key,
                    hostname: dc.hostname,
                    type: dc.device_type
                }
        )
        
        // Prosečan broj konekcija po uređaju
        LET avg_connections = AVG(
            FOR dc IN device_connections
                RETURN dc.connection_count
        )
        
        // Statistika portova
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
        
        // VLAN statistika
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
        
        // Statistika statičkih ruta
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
        """
        
        cursor = db.aql.execute(query)
        stats = next(cursor)
        
        return {
            "statistics": stats,
            "database": get_current_database_name()
        }
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Analiza Mrežnih Putanja
@app.get("/api/paths/analyze")
def analyze_paths(
    source_key: str,
    target_key: str,
    db: StandardDatabase = Depends(get_db)
):
    """
    Pronalazak svih mogućih putanja između dva uređaja sa analizom troškova
    
    Vraća:
    - shortest_path: Putanja sa minimalnim brojem skokova (zelena)
    - cheapest_path: Putanja sa najnižom cenom na osnovu brzine kabla (crvena)
    - alternative_paths: Druge održive putanje (žuta)
    
    Računanje troškova:
    - 10G = 1, 25G = 1, 40G = 1, 100G = 1 (visoka brzina, niska cena)
    - 1G = 5 (standardna cena)
    - 100M = 10 (viša cena)
    - 10M = 20 (najviša cena)
    """
    try:
        devices_col = get_devices_collection()
        
        # Provera da oba uređaja postoje
        source = devices_col.get(source_key)
        target = devices_col.get(target_key)
        
        if not source:
            raise HTTPException(status_code=404, detail=f"Source device '{source_key}' not found")
        if not target:
            raise HTTPException(status_code=404, detail=f"Target device '{target_key}' not found")
        
        source_id = f"devices/{source_key}"
        target_id = f"devices/{target_key}"
        
        # Debug: Provera da li konekcije postoje
        connections_col = get_connections_collection()
        all_connections = list(connections_col.all())
        print(f"\n=== PATH ANALYSIS DEBUG ===")
        print(f"Source: {source_id} ({source.get('hostname')})")
        print(f"Target: {target_id} ({target.get('hostname')})")
        print(f"Total connections in DB: {len(all_connections)}")
        for conn in all_connections:
            print(f"  {conn['_from']} -> {conn['_to']} (ports: {conn.get('src_port')} -> {conn.get('dst_port')})")
        
        # AQL upit za pronalazak svih putanja sa različitim strategijama
        query = """
        LET source_id = @source_id
        LET target_id = @target_id
        
        // Pronalazak SVIH putanja između izvora i cilja (limit dubine za sprečavanje beskonačnih petlji)
        // Korišćenje ANY umesto OUTBOUND da bi se omogućio dvosmerni prolaz (mrežni kablovi rade u oba smera)
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
        
        // Računanje troškova za svaku putanju na osnovu brzine kabla
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
        
        // Pronalazak najkraće putanje (minimalni broj skokova)
        LET shortest = (
            FOR path IN paths_with_cost
                SORT path.hop_count ASC, path.total_cost ASC
                LIMIT 1
                RETURN path
        )[0]
        
        // Pronalazak najjeftinije putanje (minimalna cena)
        LET cheapest = (
            FOR path IN paths_with_cost
                SORT path.total_cost ASC, path.hop_count ASC
                LIMIT 1
                RETURN path
        )[0]
        
        // Pronalazak alternativnih putanja (ne najkraćih, ne najjeftinijih, sortiranih po kvalitetu)
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
        """
        
        cursor = db.aql.execute(query, bind_vars={
            'source_id': source_id,
            'target_id': target_id
        })
        
        result = next(cursor)
        
        # Formatiranje putanja za frontend
        def format_path(path_data):
            if not path_data:
                return None
            
            # Izgradnja mape ključeva uređaja ka hostname-ovima
            device_map = {v['_key']: v['hostname'] for v in path_data['vertices']}
            
            return {
                'hops': path_data['hop_count'],
                'cost': path_data['total_cost'],
                'avg_cost': round(path_data['avg_cost'], 2),
                'devices': [
                    {
                        'key': v['_key'],
                        'hostname': v['hostname'],
                        'device_type': v['device_type']
                    }
                    for v in path_data['vertices']
                ],
                'connections': [
                    {
                        'key': e['_key'],
                        'from': e['_from'].split('/')[-1],
                        'to': e['_to'].split('/')[-1],
                        'from_hostname': device_map.get(e['_from'].split('/')[-1], 'Unknown'),
                        'to_hostname': device_map.get(e['_to'].split('/')[-1], 'Unknown'),
                        'src_port': e.get('src_port', 'N/A'),
                        'dst_port': e.get('dst_port', 'N/A'),
                        'speed': e.get('speed', '1G'),
                        'cable_type': e.get('cable_type', 'unknown')
                    }
                    for e in path_data['edges']
                ]
            }
        
        return {
            'source': {
                'key': result['source']['_key'],
                'hostname': result['source']['hostname'],
                'device_type': result['source']['device_type']
            },
            'target': {
                'key': result['target']['_key'],
                'hostname': result['target']['hostname'],
                'device_type': result['target']['device_type']
            },
            'shortest_path': format_path(result['shortestPath']),
            'cheapest_path': format_path(result['cheapestPath']),
            'alternative_paths': [format_path(p) for p in result['alternativePaths']],
            'total_paths_found': result['totalPathsFound'],
            'database': get_current_database_name()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# Operacije Evidencije Revizije
@app.get("/api/audit-log")
def get_audit_log(
    limit: int = 100,
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    db: StandardDatabase = Depends(get_db)
):
    """
    Preuzimanje unosa evidencije revizije sa opcionim filtriranjem
    
    Query Parametri:
    - limit: Maksimalan broj unosa za vraćanje (podrazumevano: 100, max: 1000)
    - action: Filtriranje po tipu radnje (create, update, delete, bulk_save)
    - entity_type: Filtriranje po tipu entiteta (device, connection, topology)
    """
    try:
        audit_col = get_audit_log_collection()
        
        # Izgradnja AQL upita sa filterima
        filters = []
        bind_vars = {'limit': min(limit, 1000)}
        
        if action:
            filters.append("doc.action == @action")
            bind_vars['action'] = action
        
        if entity_type:
            filters.append("doc.entity_type == @entity_type")
            bind_vars['entity_type'] = entity_type
        
        filter_clause = " AND ".join(filters) if filters else "true"
        
        query = f"""
        FOR doc IN {audit_col.name}
            FILTER {filter_clause}
            SORT doc.timestamp DESC
            LIMIT @limit
            RETURN doc
        """
        
        cursor = db.aql.execute(query, bind_vars=bind_vars)
        entries = [doc for doc in cursor]
        
        return {
            "total": len(entries),
            "entries": entries,
            "database": get_current_database_name()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/audit-log/stats")
def get_audit_log_stats(db: StandardDatabase = Depends(get_db)):
    """Dobijanje statistike i rezimea evidencije revizije"""
    try:
        audit_col = get_audit_log_collection()
        
        # Agregacija statistike koristeći AQL
        query = """
        LET total = LENGTH(FOR doc IN @@collection RETURN 1)
        
        LET by_action = (
            FOR doc IN @@collection
                COLLECT action = doc.action WITH COUNT INTO count
                RETURN {action: action, count: count}
        )
        
        LET by_entity = (
            FOR doc IN @@collection
                COLLECT entity_type = doc.entity_type WITH COUNT INTO count
                RETURN {entity_type: entity_type, count: count}
        )
        
        LET recent = (
            FOR doc IN @@collection
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
        """
        
        cursor = db.aql.execute(query, bind_vars={'@collection': audit_col.name})
        stats = next(cursor)
        
        return {
            "statistics": stats,
            "database": get_current_database_name()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
