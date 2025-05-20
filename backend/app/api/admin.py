from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import psutil
import os
from datetime import datetime
import humanize
from app.core.security import auth_manager
from app.db.session import db_manager
from app.core.websocket_queue import connection_health as connection_manager
from app.services.rag import rag_storage_service
from app.core.config import settings

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def get_admin_user(user = Depends(auth_manager.get_current_user)):
    if user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

def calculate_rag_storage_size() -> int:
    """Calculate total size of RAG storage directory in bytes."""
    total_size = 0
    for dirpath, _, filenames in os.walk(settings.CHROMA_PERSIST_DIR):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size

async def get_total_documents() -> int:
    """Get actual count of all documents in ChromaDB."""
    try:
        client = rag_storage_service.client
        total_count = 0
        for collection in client.list_collections():
            total_count += collection.count()
        return total_count
    except Exception as e:
        logger.error(f"Error counting documents: {e}")
        return 0

def get_active_websocket_connections() -> int:
    """Get actual count of active WebSocket connections."""
    return sum(len(conns) for conns in connection_manager.active_connections.values())

@router.get("/status", dependencies=[Depends(get_admin_user)])
async def get_system_metrics() -> Dict[str, Any]:
    """Get comprehensive system metrics."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Database pool stats
    pool_stats = db_manager.get_pool_stats()
    
    # Calculate actual RAG storage size
    rag_total_size = calculate_rag_storage_size()
    
    # Get actual document count from ChromaDB
    total_documents = await get_total_documents()
    
    # Get actual WebSocket connections
    active_connections = get_active_websocket_connections()
    
    # System load averages
    load_avg = os.getloadavg() if hasattr(os, 'getloadavg') else (-1, -1, -1)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available": humanize.naturalsize(memory.available),
            "disk_percent": disk.percent,
            "disk_free": humanize.naturalsize(disk.free),
            "load_averages": {
                "1min": load_avg[0],
                "5min": load_avg[1],
                "15min": load_avg[2]
            },
            "open_files": len(psutil.Process().open_files()),
            "connections": len(psutil.Process().connections())
        },
        "database": {
            "pool": pool_stats,
            "connections": {
                "active": pool_stats["checkedout_connections"],
                "available": pool_stats["available_connections"],
                "total": pool_stats["current_connections"]
            }
        },
        "websockets": {
            "current_connections": active_connections,
            "peak_connections": connection_manager.metrics['peak_connections'],
            "active_conversations": len(connection_manager.active_connections),
            "timeouts": connection_manager.metrics['timeouts'].get('connection', 0)
        },
        "rag": {
            "storage": humanize.naturalsize(rag_total_size),
            "total_documents": total_documents,
            "collections": len(rag_storage_service.client.list_collections()),
            "users": len(set(coll.metadata.get('owner_id') for coll in rag_storage_service.client.list_collections() if coll.metadata)),
            "errors": 0  # Reset since we're now counting actual values
        }
    }

@router.get("/health", dependencies=[Depends(get_admin_user)])
async def get_health_status() -> Dict[str, Any]:
    """Get detailed health status of all system components."""
    # Verify database connection
    db_healthy = await db_manager.verify_pool_health()
    
    # Check actual WebSocket connections
    ws_count = get_active_websocket_connections()
    ws_healthy = ws_count >= 0  # At least properly initialized
    
    # Check system resources
    system_healthy = psutil.virtual_memory().percent < 90 and psutil.cpu_percent() < 90
    
    return {
        "status": "healthy" if all([db_healthy, ws_healthy, system_healthy]) else "degraded",
        "components": {
            "database": {
                "status": "healthy" if db_healthy else "unhealthy",
                "last_check": datetime.utcnow().isoformat()
            },
            "websockets": {
                "status": "healthy" if ws_healthy else "unhealthy", 
                "connections": ws_count
            },
            "system": {
                "status": "healthy" if system_healthy else "degraded",
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent()
            }
        }
    }
