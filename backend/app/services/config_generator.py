# backend/app/services/config_generator.py
"""
Generator konfiguracionih fajlova
Konvertuje ArangoDB graf podatke u mrežne konfiguracione fajlove
"""

from typing import List, Dict, Any
from datetime import datetime


class ConfigGenerator:
    """Generisanje mrežnih konfiguracionih fajlova iz graf podataka"""
    
    @staticmethod
    def generate_network_diagram_text(devices: List[Dict]) -> str:
        """
        Generisanje ASCII tekstualne reprezentacije mrežne topologije
        
        Argumenti:
            devices: Lista rečnika uređaja
            
        Vraća:
            Tekstualni dijagram kao string
        """
        output = []
        output.append("Network Topology Diagram")
        output.append("=" * 80)
        output.append("")
        
        # Grupisanje po tipu
        routers = [d for d in devices if d['device_type'] == 'router']
        switches = [d for d in devices if d['device_type'] == 'switch']
        servers = [d for d in devices if d['device_type'] == 'server']
        
        # Sloj rutera
        if routers:
            output.append("ROUTERS (Core Layer)")
            output.append("-" * 40)
            for router in routers:
                output.append(f"[{router['hostname']}] {router['ip_address']}")
                if router['connections']:
                    for conn in router['connections']:
                        output.append(f"  └─ {conn['my_port']} ──→ {conn['neighbor_hostname']}:{conn['neighbor_port']}")
            output.append("")
        
        # Sloj svičeva
        if switches:
            output.append("SWITCHES (Distribution/Access Layer)")
            output.append("-" * 40)
            for switch in switches:
                output.append(f"[{switch['hostname']}] {switch['ip_address']}")
                if switch['connections']:
                    for conn in switch['connections']:
                        output.append(f"  └─ {conn['my_port']} ──→ {conn['neighbor_hostname']}:{conn['neighbor_port']}")
            output.append("")
        
        # Sloj servera
        if servers:
            output.append("SERVERS (End Devices)")
            output.append("-" * 40)
            for server in servers:
                output.append(f"[{server['hostname']}] {server['ip_address']}")
                if server['connections']:
                    for conn in server['connections']:
                        output.append(f"  └─ {conn['my_port']} ──→ {conn['neighbor_hostname']}:{conn['neighbor_port']}")
            output.append("")
        
        return "\n".join(output)
    
    @staticmethod
    def generate_cisco_style_config(devices: List[Dict]) -> str:
        """
        Generisanje Cisco IOS-stil konfiguracionih komandi
        
        Argumenti:
            devices: Lista rečnika uređaja
            
        Vraća:
            Cisco-stil konfiguraciju kao string
        """
        output = []
        output.append("! NetGraph Provisioner - Cisco IOS Style Configuration")
        output.append(f"! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("!")
        output.append("")
        
        for device in devices:
            output.append("!" + "=" * 70)
            output.append(f"! Device: {device['hostname']}")
            output.append("!" + "=" * 70)
            output.append("")
            output.append(f"hostname {device['hostname']}")
            output.append("!")
            
            # Konfiguracija Router ID-a za ruting protokole (OSPF, EIGRP, BGP)
            router_id = device.get('router_id')
            if router_id and device['device_type'] in ['l3_switch', 'router']:
                output.append(f"! Router ID for routing protocols")
                output.append(f"router-id {router_id}")
                output.append("!")
            
            # Omogućavanje IP rutiranja za L3 svičeve i rutere (za inter-VLAN rutiranje)
            if device['device_type'] in ['l3_switch', 'router']:
                output.append("ip routing")
                output.append("!")
            
            # Konfiguracija VLAN baze podataka (za svičeve i L3 svičeve)
            vlans = device.get('vlans', [])
            if vlans and device['device_type'] in ['switch', 'l3_switch']:
                output.append("! VLAN Database")
                for vlan in vlans:
                    vlan_id = vlan.get('vlan_id')
                    vlan_name = vlan.get('name', f'VLAN{vlan_id}')
                    vlan_status = vlan.get('status', 'active')
                    
                    output.append(f"vlan {vlan_id}")
                    output.append(f" name {vlan_name}")
                    if vlan_status == 'suspended':
                        output.append(" shutdown")
                    output.append("!")
            
            # Konfiguracija interfejsa
            # Prvo, mapiraj sve definisane portove po imenu za lakšu pretragu
            defined_ports = {p.get('name'): p for p in device.get('ports', [])}
            
            if device['connections']:
                for conn in device['connections']:
                    port_name = conn['my_port']
                    port_config = defined_ports.get(port_name, {})
                    
                    output.append(f"interface {port_name}")
                    output.append(f" description Connected to {conn['neighbor_hostname']} port {conn['neighbor_port']}")
                    
                    # Konfiguracija brzine i dupleksa iz konekcije
                    speed_map = {
                        '10M': '10', '100M': '100', '1G': '1000', 
                        '10G': '10000', '25G': '25000', '40G': '40000', '100G': '100000'
                    }
                    conn_speed = conn.get('speed', '1G')
                    conn_duplex = conn.get('duplex', 'auto')
                    
                    if conn_speed in speed_map:
                        output.append(f" speed {speed_map[conn_speed]}")
                    
                    if conn_duplex != 'auto':
                        output.append(f" duplex {conn_duplex}")
                    elif conn_duplex == 'auto':
                        output.append(" speed auto")
                        output.append(" duplex auto")
                    
                    # 1. Provera da li je ovo L3 svič rutirani port
                    if device['device_type'] == 'l3_switch' and port_config.get('is_routed'):
                        output.append(" no switchport")
                        if port_config.get('ip_address'):
                            mask = port_config.get('subnet_mask', '255.255.255.0')
                            output.append(f" ip address {port_config['ip_address']} {mask}")
                    
                    # 2. Provera za specifičnu Layer 3 IP na portu
                    elif port_config.get('ip_address'):
                        mask = port_config.get('subnet_mask', '255.255.255.0')
                        output.append(f" ip address {port_config['ip_address']} {mask}")
                    
                    # 3. Provera za Layer 2 VLAN konfiguraciju
                    elif port_config.get('mode') == 'trunk':
                        output.append(" switchport mode trunk")
                        if port_config.get('vlan'):
                            output.append(f" switchport trunk allowed vlan {port_config['vlan']}")
                    elif port_config.get('mode') == 'access':
                        output.append(" switchport mode access")
                        if port_config.get('vlan'):
                            output.append(f" switchport access vlan {port_config['vlan']}")
                            
                    # 4. Rezervna logika za stari menadžment IP samo za Rutere na prvom portu ako specifična IP nije postavljena
                    elif device['device_type'] == 'router' and port_name in ['eth0', 'GigabitEthernet0/0'] and device.get('ip_address'):
                         output.append(f" ip address {device['ip_address']} {device.get('subnet_mask', '255.255.255.0')}")
                    
                    output.append(" no shutdown")
                    output.append("!")
            
            # Koristi 'ports' definiciju za generisanje subinterfejsa, SVI-jeva ili nepovezanih unapred konfigurisanih portova
            for p_name, p_data in defined_ports.items():
                # Preskoči ako je već obrađeno u petlji konekcija
                if any(c['my_port'] == p_name for c in device['connections']):
                    continue
                
                # Obrada Loopback interfejsa
                if p_data.get('type') == 'loopback' or p_name.lower().startswith('loopback'):
                    output.append(f"interface {p_name}")
                    if p_data.get('description'):
                        output.append(f" description {p_data['description']}")
                    if p_data.get('ip_address'):
                        mask = p_data.get('subnet_mask', '255.255.255.255')
                        output.append(f" ip address {p_data['ip_address']} {mask}")
                    output.append(" no shutdown")
                    output.append("!")
                    continue
                
                # Obrada SVI (Switch Virtual Interface)
                if p_data.get('is_svi'):
                    vlan_id = p_data.get('vlan_id') or p_name.replace('vlan', '')
                    output.append(f"interface vlan {vlan_id}")
                    if p_data.get('description'):
                        output.append(f" description {p_data['description']}")
                    if p_data.get('ip_address'):
                        mask = p_data.get('subnet_mask', '255.255.255.0')
                        output.append(f" ip address {p_data['ip_address']} {mask}")
                    output.append(" no shutdown")
                    output.append("!")
                    continue
                
                # Obrada subinterfejsa ili Layer 3 portova sa konfigurisanom IP
                if '.' in p_name or p_data.get('ip_address') or p_data.get('vlan_id'):
                     output.append(f"interface {p_name}")
                     if p_data.get('description'):
                         output.append(f" description {p_data['description']}")
                     
                     # Enkapsulacija subinterfejsa (za rutere)
                     if ('.' in p_name or p_data.get('vlan_id')) and not p_data.get('is_svi'):
                         # Koristi eksplicitni vlan_id ako je pružen, inače parsiraj iz imena
                         vlan_id = p_data.get('vlan_id') or p_name.split('.')[-1]
                         encap = p_data.get('encapsulation', 'dot1Q')
                         output.append(f" encapsulation {encap} {vlan_id}")

                     if p_data.get('ip_address'):
                         mask = p_data.get('subnet_mask', '255.255.255.0')
                         output.append(f" ip address {p_data['ip_address']} {mask}")
                     
                     output.append(" no shutdown")
                     output.append("!")

            # Konfiguracija statičkih ruta
            static_routes = device.get('static_routes', [])
            if static_routes:
                output.append("! Static Routes")
                for route in static_routes:
                    dest_net = route.get('destination_network', '')
                    mask = route.get('subnet_mask', '')
                    next_hop = route.get('next_hop', '')
                    exit_int = route.get('exit_interface', '')
                    metric = route.get('metric', 1)
                    description = route.get('description', '')
                    
                    if description:
                        output.append(f"! {description}")
                    
                    # Build the route command
                    route_cmd = f"ip route {dest_net} {mask}"
                    
                    # Dodaj next-hop i/ili izlazni interfejs
                    if next_hop and exit_int:
                        route_cmd += f" {exit_int} {next_hop}"
                    elif next_hop:
                        route_cmd += f" {next_hop}"
                    elif exit_int:
                        route_cmd += f" {exit_int}"
                    
                    # Dodaj metriku ako nije podrazumevana
                    if metric and metric != 1:
                        route_cmd += f" {metric}"
                    
                    output.append(route_cmd)
                output.append("!")

            output.append("")
        
        output.append("end")
        
        return "\n".join(output)
    
    @staticmethod
    def generate_json_export(devices: List[Dict]) -> Dict[str, Any]:
        """
        Izvoz topologije kao strukturirani JSON
        
        Argumenti:
            devices: Lista rečnika uređaja
            
        Vraća:
            JSON-serijalizabilan rečnik
        """
        return {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "generator": "NetGraph Provisioner",
                "version": "1.0"
            },
            "topology": {
                "devices": devices,
                "statistics": {
                    "total_devices": len(devices),
                    "routers": len([d for d in devices if d['device_type'] == 'router']),
                    "switches": len([d for d in devices if d['device_type'] == 'switch']),
                    "servers": len([d for d in devices if d['device_type'] == 'server']),
                    "total_connections": sum(len(d['connections']) for d in devices) // 2  # Podeliti sa 2 jer su konekcije dvosmerne
                }
            }
        }


# Example usage function
def generate_config_from_graph(devices_data: List[Dict], format: str = "cisco") -> str:
    """
    Glavna funkcija za generisanje konfiguracije u zadatom formatu
    
    Argumenti:
        devices_data: Izlaz iz GraphService.get_port_connection_map()
        format: Jedan od 'cisco', 'diagram', 'json'
        
    Vraća:
        Konfiguracija kao string
    """
    generator = ConfigGenerator()
    
    if format == "cisco":
        return generator.generate_cisco_style_config(devices_data)
    elif format == "diagram":
        return generator.generate_network_diagram_text(devices_data)
    elif format == "json":
        import json
        return json.dumps(generator.generate_json_export(devices_data), indent=2)
    else:
        raise ValueError(f"Unknown format: {format}")
