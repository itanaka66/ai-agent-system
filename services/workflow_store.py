"""
Workflow Config Store
Reads/writes the node-graph JSON files under configs/workflow_configs/
that back the visual workflow builder.
"""

import json
import os
import re
import threading
from pathlib import Path
from typing import Dict, List

WORKFLOW_DIR = Path(__file__).resolve().parent.parent / "configs" / "workflow_configs"

_lock = threading.Lock()

VALID_NODE_TYPES = {"START_NODE", "THINKER_AGENT", "VALIDATOR_AGENT", "EXECUTOR_AGENT", "END_NODE"}
_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]+$")


class WorkflowStoreError(ValueError):
    pass


def _safe_path(name: str) -> Path:
    if not name or not _NAME_RE.match(name):
        raise WorkflowStoreError("Workflow name must be alphanumeric/underscore/hyphen only")
    return WORKFLOW_DIR / f"{name}.json"


def validate_workflow(data: Dict) -> None:
    if not isinstance(data, dict):
        raise WorkflowStoreError("Workflow must be a JSON object")

    nodes = data.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise WorkflowStoreError("Workflow must contain a non-empty 'nodes' list")

    seen_ids = set()
    start_count = 0
    end_count = 0

    for node in nodes:
        if not isinstance(node, dict):
            raise WorkflowStoreError("Each node must be an object")

        node_id = node.get("id")
        node_type = node.get("type")

        if not node_id or not isinstance(node_id, str):
            raise WorkflowStoreError("Every node needs a string 'id'")
        if node_id in seen_ids:
            raise WorkflowStoreError(f"Duplicate node id '{node_id}'")
        seen_ids.add(node_id)

        if node_type not in VALID_NODE_TYPES:
            raise WorkflowStoreError(f"Node '{node_id}' has invalid type '{node_type}'")

        position = node.get("position")
        if not (isinstance(position, list) and len(position) == 2):
            raise WorkflowStoreError(f"Node '{node_id}' needs a [x, y] 'position'")

        for io_key in ("inputs", "outputs"):
            io_list = node.get(io_key, [])
            if not isinstance(io_list, list):
                raise WorkflowStoreError(f"Node '{node_id}' field '{io_key}' must be a list")
            io_name = "input" if io_key == "inputs" else "output"
            for entry in io_list:
                if not isinstance(entry, dict) or io_name not in entry:
                    raise WorkflowStoreError(f"Node '{node_id}' has a malformed '{io_key}' entry")

        if node_type == "START_NODE":
            start_count += 1
        elif node_type == "END_NODE":
            end_count += 1

    if start_count != 1:
        raise WorkflowStoreError("Workflow must contain exactly one START_NODE")
    if end_count != 1:
        raise WorkflowStoreError("Workflow must contain exactly one END_NODE")


def list_workflows() -> List[Dict]:
    if not WORKFLOW_DIR.exists():
        return []

    results = []
    with _lock:
        for path in sorted(WORKFLOW_DIR.glob("*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                continue
            results.append({
                "name": path.stem,
                "display_name": data.get("name", path.stem),
                "description": data.get("description", ""),
                "node_count": len(data.get("nodes", [])),
            })
    return results


def get_workflow(name: str) -> Dict:
    path = _safe_path(name)
    if not path.exists():
        raise WorkflowStoreError(f"Workflow '{name}' not found")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_workflow(name: str, data: Dict) -> Dict:
    validate_workflow(data)
    path = _safe_path(name)

    with _lock:
        WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(".json.tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)

    return data


def delete_workflow(name: str) -> None:
    path = _safe_path(name)
    with _lock:
        if not path.exists():
            raise WorkflowStoreError(f"Workflow '{name}' not found")
        path.unlink()
