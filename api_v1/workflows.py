"""
Workflow Builder API
CRUD for visual agent workflows (configs/workflow_configs/*.json) plus a
'run' endpoint so a workflow can be test-executed straight from the builder UI.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services import workflow_store
from core.workflow_engine import run_workflow, WorkflowExecutionError

router = APIRouter(prefix="/workflows", tags=["workflows"])


class WorkflowRunRequest(BaseModel):
    query: str


@router.get("")
async def list_workflows():
    return {"workflows": workflow_store.list_workflows()}


@router.get("/{name}")
async def get_workflow(name: str):
    try:
        return workflow_store.get_workflow(name)
    except workflow_store.WorkflowStoreError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{name}")
async def save_workflow(name: str, payload: Dict[str, Any]):
    try:
        return workflow_store.save_workflow(name, payload)
    except workflow_store.WorkflowStoreError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{name}")
async def delete_workflow(name: str):
    try:
        workflow_store.delete_workflow(name)
    except workflow_store.WorkflowStoreError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"deleted": name}


@router.post("/{name}/run")
async def run_workflow_endpoint(name: str, payload: WorkflowRunRequest):
    """Execute a saved workflow against a test query (requires reachable Ollama nodes)."""
    try:
        workflow = workflow_store.get_workflow(name)
    except workflow_store.WorkflowStoreError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        return await run_workflow(workflow, payload.query)
    except WorkflowExecutionError as e:
        raise HTTPException(status_code=502, detail=str(e))
