# backend/app/database.py
"""
Povezivanje i inicijalizacija ArangoDB baze podataka - Podrška za više baza podataka
"""

from arango import ArangoClient
from arango.database import StandardDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Konfiguracija
ARANGO_HOST = os.getenv('ARANGO_HOST', 'http://localhost:8529')
ARANGO_USER = os.getenv('ARANGO_USER', 'root')
ARANGO_PASSWORD = os.getenv('ARANGO_PASSWORD', '')  # Prazna lozinka za lokalnu instalaciju
GRAPH_NAME = 'network_topology'
DEVICES_COLLECTION = 'devices'
CONNECTIONS_COLLECTION = 'connections'
AUDIT_LOG_COLLECTION = 'audit_log'


class ArangoDBConnection:
    """Menadžer povezivanja baze podataka za više ArangoDB baza podataka"""
    
    _instance = None
    _client = None
    _sys_db = None
    _current_db: StandardDatabase = None
    _current_db_name = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ArangoDBConnection, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._client is None:
            self._connect_client()
    
    def _connect_client(self):
        """Uspostavljanje veze sa ArangoDB sistemskom bazom podataka"""
        try:
            print(f"Connecting to ArangoDB at {ARANGO_HOST}...")
            self._client = ArangoClient(hosts=ARANGO_HOST)
            self._sys_db = self._client.db('_system', username=ARANGO_USER, password=ARANGO_PASSWORD)
            print(f"Connected to ArangoDB system database")
        except Exception as e:
            print(f"Failed to connect to ArangoDB: {e}")
            print(f"Make sure ArangoDB is running at {ARANGO_HOST}")
            raise
    
    def connect_to_database(self, db_name: str):
        """Povezivanje sa određenom bazom podataka i inicijalizacija šeme"""
        try:
            # Provera da li baza podataka postoji
            if not self._sys_db.has_database(db_name):
                raise Exception(f"Database '{db_name}' does not exist")
            
            # Povezivanje sa bazom podataka
            self._current_db = self._client.db(db_name, username=ARANGO_USER, password=ARANGO_PASSWORD)
            self._current_db_name = db_name
            
            # Inicijalizacija kolekcija ako je potrebno
            self._initialize_schema()
            
            print(f"Connected to database: {db_name}")
            return self._current_db
        except Exception as e:
            print(f"Failed to connect to database '{db_name}': {e}")
            raise
    
    def create_database(self, db_name: str):
        """Kreiranje nove ArangoDB baze podataka sa standardnim kolekcijama"""
        try:
            print(f"Attempting to create database: '{db_name}' inside _system db")
            # Provera da li baza podataka već postoji
            if self._sys_db.has_database(db_name):
                print(f"Database '{db_name}' already exists")
                # Čak i ako postoji, pokušavamo da se povežemo kako bismo osigurali šemu
                return self.connect_to_database(db_name)
            
            # Kreiranje baze podataka
            self._sys_db.create_database(db_name)
            print(f"Database '{db_name}' created successfully")
            
            # Povezivanje i inicijalizacija šeme
            return self.connect_to_database(db_name)
        except Exception as e:
            print(f"Failed to create database '{db_name}': {e}")
            raise
    
    def list_databases(self, prefix='netgraph_'):
        """Izlistavanje svih baza podataka sa zadatim prefiksom"""
        try:
            all_dbs = self._sys_db.databases()
            # Filtriranje za prikaz samo netgraph baza podataka
            filtered_dbs = [db for db in all_dbs if db.startswith(prefix)]
            return filtered_dbs
        except Exception as e:
            print(f"Failed to list databases: {e}")
            raise
    
    def delete_database(self, db_name: str):
        """Brisanje baze podataka"""
        try:
            if db_name == '_system':
                raise Exception("Cannot delete system database")
            
            self._sys_db.delete_database(db_name)
            print(f"Database '{db_name}' deleted")
            
            # Brisanje trenutne veze ako smo obrisali aktivnu bazu podataka
            if self._current_db_name == db_name:
                self._current_db = None
                self._current_db_name = None
        except Exception as e:
            print(f"Failed to delete database '{db_name}': {e}")
            raise
    
    @property
    def db(self):
        """Dobijanje trenutne veze sa bazom podataka"""
        if self._current_db is None:
            raise Exception("No database connected. Please select a database first.")
        return self._current_db
    
    @property
    def current_database_name(self):
        """Dobijanje imena trenutne baze podataka"""
        return self._current_db_name
    
    def _initialize_schema(self):
        """Automatsko kreiranje kolekcija, grafa i indeksa ako ne postoje"""
        if self._current_db is None:
            return
        
        # Kreiranje kolekcije čvorova (uređaja)
        if not self._current_db.has_collection(DEVICES_COLLECTION):
            devices_col = self._current_db.create_collection(DEVICES_COLLECTION)
            print(f"Collection '{DEVICES_COLLECTION}' created")
            
            # Kreiranje indeksa na kolekciji uređaja
            devices_col.add_hash_index(fields=['hostname'], unique=False)
            devices_col.add_hash_index(fields=['device_type'], unique=False)
            devices_col.add_hash_index(fields=['ip_address'], unique=False)
            print(f"Indexes created on '{DEVICES_COLLECTION}'")
        
        # Kreiranje edge kolekcije (konekcija)
        if not self._current_db.has_collection(CONNECTIONS_COLLECTION):
            connections_col = self._current_db.create_collection(CONNECTIONS_COLLECTION, edge=True)
            print(f"Edge collection '{CONNECTIONS_COLLECTION}' created")
            
            # Kreiranje indeksa na konekcijama
            connections_col.add_hash_index(fields=['cable_type'], unique=False)
            connections_col.add_hash_index(fields=['status'], unique=False)
            print(f"Indexes created on '{CONNECTIONS_COLLECTION}'")
        
        # Kreiranje kolekcije za evidenciju revizije (skladište dokumenata za praćenje promena)
        if not self._current_db.has_collection(AUDIT_LOG_COLLECTION):
            audit_col = self._current_db.create_collection(AUDIT_LOG_COLLECTION)
            print(f"Collection '{AUDIT_LOG_COLLECTION}' created")
            
            # Kreiranje indeksa na evidenciji revizije
            audit_col.add_hash_index(fields=['action'], unique=False)
            audit_col.add_hash_index(fields=['entity_type'], unique=False)
            audit_col.add_hash_index(fields=['entity_id'], unique=False)
            audit_col.add_skiplist_index(fields=['timestamp'], unique=False)
            print(f"Indexes created on '{AUDIT_LOG_COLLECTION}'")
        
        # Kreiranje definicije grafa
        if not self._current_db.has_graph(GRAPH_NAME):
            graph = self._current_db.create_graph(GRAPH_NAME)
            
            # Definisanje edge definicije (konekcije povezuju uređaje sa uređajuma)
            graph.create_edge_definition(
                edge_collection=CONNECTIONS_COLLECTION,
                from_vertex_collections=[DEVICES_COLLECTION],
                to_vertex_collections=[DEVICES_COLLECTION]
            )
            
            print(f"Graph '{GRAPH_NAME}' created with edge definition")


# Singleton instanca
arango_connection = ArangoDBConnection()


def get_db() -> StandardDatabase:
    """
    Injekcija zavisnosti za FastAPI rute
    Upotreba: db: StandardDatabase = Depends(get_db)
    """
    return arango_connection.db


def get_devices_collection():
    """Dobijanje kolekcije uređaja iz trenutne baze podataka"""
    return arango_connection.db.collection(DEVICES_COLLECTION)


def get_connections_collection():
    """Dobijanje kolekcije konekcija iz trenutne baze podataka"""
    return arango_connection.db.collection(CONNECTIONS_COLLECTION)


def list_databases():
    """Izlistavanje svih NetGraph baza podataka"""
    return arango_connection.list_databases()


def create_database(db_name: str):
    """Kreiranje nove baze podataka"""
    # Osiguravanje da ima netgraph prefiks
    if not db_name.startswith('netgraph_'):
        db_name = f"netgraph_{db_name}"
    return arango_connection.create_database(db_name)


def connect_to_database(db_name: str):
    """Povezivanje sa određenom bazom podataka"""
    return arango_connection.connect_to_database(db_name)


def delete_database(db_name: str):
    """Brisanje baze podataka"""
    return arango_connection.delete_database(db_name)


def get_current_database_name():
    """Dobijanje imena trenutno povezane baze podataka"""
    return arango_connection.current_database_name


def get_audit_log_collection():
    """Dobijanje kolekcije evidencije revizije"""
    db = arango_connection.db
    return db.collection(AUDIT_LOG_COLLECTION)


def log_audit_event(action: str, entity_type: str, entity_id: str, entity_data: dict, user: str = "system"):
    """
    Beleženje događaja revizije u kolekciju evidencije revizije
    
    Argumenti:
        action: Izvršena radnja (create, update, delete, bulk_save)
        entity_type: Tip entiteta (device, connection, topology)
        entity_id: ID ili ključ entiteta
        entity_data: Snimak podataka entiteta
        user: Korisnik koji je izvršio radnju
    """
    from datetime import datetime
    
    try:
        audit_col = get_audit_log_collection()
        
        audit_entry = {
            'action': action,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'entity_data': entity_data,
            'user': user,
            'timestamp': datetime.utcnow().isoformat(),
            'database': arango_connection.current_database_name
        }
        
        result = audit_col.insert(audit_entry)
        return result
    except Exception as e:
        print(f"⚠️ Failed to log audit event: {e}")
        # Ne podiži grešku - beleženje revizije ne bi trebalo da prekine glavne operacije
        return None
