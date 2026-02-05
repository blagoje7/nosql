# backend/app/services/graph_service.py
"""
Graf servis - AQL upiti i graf operacije
"""

from typing import List, Dict
from arango.database import StandardDatabase


class GraphService:
    """Servis za izvršavanje AQL graf upita"""
    
    def __init__(self, db: StandardDatabase):
        self.db = db
    
    def get_port_connection_map(self) -> List[Dict]:
        """
        Izgradnja kompletne mape povezivanja portova za sve uređaje
        
        Vraća:
            Listu uređaja sa detaljima njihovih konekcija
        """
        query = """
        FOR device IN devices
          LET connections = (
            FOR v, e IN 1..1 ANY device._id
              GRAPH 'network_topology'
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
        """
        
        cursor = self.db.aql.execute(query)
        return [doc for doc in cursor]
