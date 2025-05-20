# In app/api/agents.py

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Any
from app.services.agents.agent_manager import agent_manager
from app.core.security import auth_manager
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import db_manager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/agents/available", response_model=List[str])
async def get_available_agents(
    current_user = Depends(auth_manager.get_current_user),
    db: AsyncSession = Depends(db_manager.get_session)
) -> List[str]:
    """Get list of available agent types."""
    try:
        return agent_manager.get_available_agents()
    except Exception as e:
        logger.error(f"Error fetching available agents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching available agents: {str(e)}"
        )

@router.get("/agents/descriptions", response_model=Dict[str, str])
async def get_agent_descriptions(
    current_user = Depends(auth_manager.get_current_user),
    db: AsyncSession = Depends(db_manager.get_session)
) -> Dict[str, str]:
    """Get descriptions for all available agents."""
    try:
        return agent_manager.get_agent_descriptions()
    except Exception as e:
        logger.error(f"Error fetching agent descriptions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching agent descriptions: {str(e)}"
        )

@router.get("/agents/collaboration-patterns")
async def get_collaboration_patterns(
    current_user = Depends(auth_manager.get_current_user),
    db: AsyncSession = Depends(db_manager.get_session)
) -> Dict[str, Any]:
    """Get analysis of agent collaboration patterns"""
    if not current_user or current_user.role != 'admin':
        raise HTTPException(status_code=403, detail="Not authorized")
        
    patterns = agent_manager.collaboration_patterns
    
    # Process patterns for display
    results = {}
    for pattern, data in patterns.items():
        pattern_key = ' + '.join(sorted(pattern))
        results[pattern_key] = {
            'total_collaborations': data['count'],
            'recent_queries': data['queries'][-5:],  # Last 5 queries
            'success_rate': data['success_rate']
        }
        
    return results
