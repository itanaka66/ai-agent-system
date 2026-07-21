"""
Agent Settings API
CRUD endpoints so the web UI can graphically customize agent
model/system-prompt/temperature/... without restarting the server.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services import agent_config_store

router = APIRouter(prefix="/agents", tags=["agents"])


class AgentConfigCreate(BaseModel):
    key: str = Field(..., description="Unique identifier, e.g. 'thinker_proposal'")
    display_name: Optional[str] = None
    role: str = Field(..., description="thinker | validator | executor")
    target: str = Field(..., description="gpu_master | gpu_worker")
    model: str
    temperature: float = 0.7
    max_tokens: int = 2048
    enabled: bool = True
    system_prompt: str


class AgentConfigUpdate(BaseModel):
    display_name: Optional[str] = None
    role: Optional[str] = None
    target: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    enabled: Optional[bool] = None
    system_prompt: Optional[str] = None


@router.get("")
async def list_agents():
    """List all configurable agents"""
    return {"agents": agent_config_store.list_agents()}


@router.get("/models")
async def list_models():
    """List models available for selection (from configs/model_map.json)"""
    return {"models": agent_config_store.list_available_models()}


@router.get("/{key}")
async def get_agent(key: str):
    agent = agent_config_store.get_agent(key)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{key}' not found")
    return agent


@router.post("")
async def create_agent(payload: AgentConfigCreate):
    fields = payload.model_dump(exclude={"key"}, exclude_none=True)
    try:
        return agent_config_store.create_agent(payload.key, fields)
    except agent_config_store.AgentConfigError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{key}")
async def update_agent(key: str, payload: AgentConfigUpdate):
    fields = payload.model_dump(exclude_none=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    try:
        return agent_config_store.update_agent(key, fields)
    except agent_config_store.AgentConfigError as e:
        status = 404 if "not found" in str(e) else 400
        raise HTTPException(status_code=status, detail=str(e))


@router.delete("/{key}")
async def delete_agent(key: str):
    try:
        agent_config_store.delete_agent(key)
    except agent_config_store.AgentConfigError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"deleted": key}
