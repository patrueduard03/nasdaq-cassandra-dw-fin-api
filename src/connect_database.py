from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
import json
import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Global variables for lazy initialization
_cluster = None
_session = None

def get_session():
    """Get or create database session with lazy initialization"""
    global _cluster, _session
    
    if _session is not None:
        return _session
    
    try:
        s_c_bundle = os.getenv('SECURE_CONNECT_BUNDLE')
        s_token = os.getenv('SECURE_TOKEN')

        if not s_c_bundle or not s_token:
            raise ValueError("SECURE_CONNECT_BUNDLE and SECURE_TOKEN environment variables must be set")

        # This secure connect bundle is autogenerated when you download your SCB
        cloud_config = {
            'secure_connect_bundle': os.path.join(os.path.dirname(os.path.dirname(__file__)), s_c_bundle)
        }

        # This token JSON file is autogenerated when you download your token
        token_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), s_token)
        with open(token_path) as f:
            secrets = json.load(f)

        CLIENT_ID = secrets["clientId"]
        CLIENT_SECRET = secrets["secret"]

        auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
        
        # Configure cluster with better defaults for DataStax Astra
        _cluster = Cluster(
            cloud=cloud_config, 
            auth_provider=auth_provider,
            protocol_version=4,  # Explicitly set protocol version for compatibility
            connect_timeout=10,   # 10 second connection timeout
            control_connection_timeout=10
        )
        _session = _cluster.connect()
        _session.execute("USE lectures")

        # Test connection and log version info
        try:
            row = _session.execute("select release_version from system.local").one()
            if row:
                logger.info(f"Connected to Cassandra version: {row[0]}")
            else:
                logger.warning("Connected to Cassandra but couldn't get version")
        except Exception as version_error:
            logger.warning(f"Could not retrieve Cassandra version: {version_error}")
            
        return _session
        
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

def close_connection():
    """Close database connection"""
    global _cluster, _session
    if _session:
        _session.shutdown()
        _session = None
    if _cluster:
        _cluster.shutdown()
        _cluster = None

# For backward compatibility, provide session as a property
class SessionProxy:
    def __getattr__(self, name):
        return getattr(get_session(), name)

session = SessionProxy()